from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tomllib
import uuid
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "route_score.py"
spec = importlib.util.spec_from_file_location("route_score", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def route(values, flags=(), failures=()):
    return module.choose_route(*values, list(failures), set(flags))


def route_cli(*args):
    result = subprocess.run(
        [sys.executable, str(MODULE_PATH), *args],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def cli_error(*args):
    return subprocess.run(
        [sys.executable, str(MODULE_PATH), *args],
        capture_output=True, text=True,
    )


BASE_ARGS = ("--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0")


def test_balanced_routes_preserve_existing_score_bands():
    assert route((0, 0, 0, 0, 0)).agent == "luna_fast"
    assert route((0, 1, 1, 1, 0)).agent == "luna_worker"
    assert route((1, 2, 2, 2, 0)).agent == "luna_deep"
    assert route((2, 3, 3, 3, 0)).agent == "sol_resolver"


def test_risk_gates_and_architecture_gate_order():
    selected = route((2, 3, 3, 3, 2), {"architecture"})
    assert (selected.agent, selected.model, selected.effort) == ("sol_architect", "gpt-6-astra", "medium")

    critical = route((2, 3, 3, 4, 2), {"architecture", "migration"})
    assert (critical.agent, critical.model, critical.effort) == ("sol_guard", "gpt-6.1-sol", "high")

    explicit_luna = cli_error(
        "--explicit-model", "gpt-6-luna", "--flag", "migration", *BASE_ARGS,
    )
    assert explicit_luna.returncode != 0
    assert "conflicts with Sol High hard-risk gate" in explicit_luna.stderr
    explicit_sol_low = cli_error(
        "--explicit-model", "gpt-6.1-sol", "--explicit-effort", "low",
        "--flag", "migration", *BASE_ARGS,
    )
    assert explicit_sol_low.returncode != 0
    explicit_sol_high = route_cli(
        "--explicit-model", "gpt-6.1-sol", "--explicit-effort", "high",
        "--flag", "migration", *BASE_ARGS,
    )
    assert explicit_sol_high["requested_model"] == "gpt-6.1-sol"
    assert explicit_sol_high["requested_effort"] == "high"


def test_sensitive_and_unknown_deletion_flags_select_sol_high():
    flags = (
        "production_change", "credentials", "credential", "secrets", "secret",
        "unknown_deletion", "recursive_delete", "unknown_recursive_delete",
    )
    for flag in flags:
        selected = route((0, 0, 0, 0, 0), {flag})
        assert (selected.agent, selected.model, selected.effort) == ("sol_guard", "gpt-6.1-sol", "high")


def test_profile_models_match_every_active_route():
    cases = [
        ((0, 0, 0, 0, 0), set()),
        ((0, 1, 1, 1, 0), set()),
        ((1, 2, 2, 2, 0), set()),
        ((1, 1, 2, 2, 1), {"idempotency"}),
        ((0, 1, 1, 2, 0), {"migration"}),
        ((2, 3, 3, 3, 2), {"architecture"}),
    ]
    expected_models = {"gpt-6-luna", "gpt-6.1-sol", "gpt-6-astra"}
    for values, flags in cases:
        selected = route(values, flags)
        profile = MODULE_PATH.parents[1] / "agents" / (selected.agent.replace("_", "-") + ".toml")
        data = tomllib.loads(profile.read_text(encoding="utf-8"))
        assert (data["name"], data["model"], data["model_reasoning_effort"]) == (
            selected.agent, selected.model, selected.effort,
        )
        assert selected.model in expected_models


def test_quality_first_promotes_each_ordinary_route_once():
    cases = [
        ((0, 0, 0, 0, 0), ("luna_worker", "gpt-6-luna", "medium")),
        ((0, 1, 1, 1, 0), ("luna_deep", "gpt-6-luna", "high")),
        ((1, 2, 2, 2, 0), ("sol_resolver", "gpt-6.1-sol", "medium")),
        ((2, 3, 3, 3, 0), ("sol_guard", "gpt-6.1-sol", "high")),
    ]
    for values, expected in cases:
        selected = module.apply_quality_first(route(values))
        assert (selected.agent, selected.model, selected.effort) == expected


def test_quality_first_preserves_sol_high_and_astra_planning_routes():
    critical = route((0, 0, 0, 4, 0), {"migration"})
    architecture = route((2, 3, 3, 3, 2), {"architecture"})
    assert module.apply_quality_first(critical) == critical
    assert module.apply_quality_first(architecture) == architecture


def test_failure_kinds_only_reasoning_and_logic_affect_score_and_escalation():
    baseline = route((0, 1, 1, 1, 0))
    for ignored in ("dependency", "permission", "test", "network", "user_input"):
        selected = route((0, 1, 1, 1, 0), failures=(ignored,))
        assert selected == baseline

    reasoning = route((0, 1, 1, 1, 0), failures=("reasoning",))
    logic = route((0, 1, 1, 1, 0), failures=("logic",))
    assert reasoning.score == logic.score == baseline.score + 1
    assert route((0, 0, 0, 0, 0), {"architecture"}, ("reasoning",)).model == "gpt-6-astra"


def test_unknown_flags_and_failure_kinds_are_rejected():
    try:
        route((0, 0, 0, 0, 0), {"not_a_real_flag"})
    except ValueError as exc:
        assert "unknown flags" in str(exc)
    else:
        raise AssertionError("unknown route flag was accepted")

    try:
        route((0, 0, 0, 0, 0), failures=("not_a_failure_kind",))
    except ValueError as exc:
        assert "unknown failure kinds" in str(exc)
    else:
        raise AssertionError("unknown failure kind was accepted")


def test_quality_first_and_route_only_cli_policies():
    default = route_cli(*BASE_ARGS)
    quality = route_cli("--policy", "quality_first", *BASE_ARGS)
    route_only = route_cli("--policy", "route_only", *BASE_ARGS)
    assert default["policy_mode"] == "balanced"
    assert default["route_effort"] == "low"
    assert (quality["route_model"], quality["route_effort"]) == ("gpt-6-luna", "medium")
    assert route_only["route_model"] == "gpt-6-luna"
    assert route_only["dispatch_action"] == "route_only"
    assert route_only["dispatch_allowed"] is False


def test_natural_language_policy_controls_and_cli_conflicts():
    quality = route_cli("--user-input", "Please DO NOT optimize quota.", *BASE_ARGS)
    assert quality["policy_mode"] == "quality_first"
    route_only = route_cli("--prompt", "Route only for this task.", *BASE_ARGS)
    assert route_only["policy_mode"] == "route_only"

    conflict = cli_error("--policy", "balanced", "--user-input", "Do not optimize quota", *BASE_ARGS)
    assert conflict.returncode != 0 and "conflicts with natural-language policy" in conflict.stderr
    multi_policy = cli_error("--user-input", "Do not optimize quota; route only", *BASE_ARGS)
    assert multi_policy.returncode != 0 and "conflicting natural-language policy" in multi_policy.stderr


def test_retired_luna_phrases_are_ignored_and_removed_cli_options_rejected():
    ordinary = route_cli(
        "--user-input", "disable Luna; Use Luna only",
        "--flag", "migration", *BASE_ARGS,
    )
    assert ordinary["route_model"] == "gpt-6.1-sol"
    assert ordinary["policy_mode"] == "balanced"

    for retired in ("--disable-luna", "--use-luna-only", "--failed-attempts"):
        result = cli_error(retired, *BASE_ARGS)
        assert result.returncode != 0 and "unrecognized arguments" in result.stderr
    retired_flag = cli_error("--flag", "use_luna_only", *BASE_ARGS)
    assert retired_flag.returncode != 0 and "invalid choice" in retired_flag.stderr


def test_subagent_policy_is_separate_from_route_recommendation():
    automatic = route_cli(*BASE_ARGS)
    denied = route_cli("--subagents", "deny", *BASE_ARGS)
    assert automatic["route_model"] == denied["route_model"] == "gpt-6-luna"
    assert automatic["dispatch_allowed"] is True
    assert denied["dispatch_allowed"] is False
    assert denied["dispatch_action"] == "blocked_subagent_policy"
    assert denied["blocker_kind"] == "subagents_denied_parent_mismatch"
    assert denied["status"] == "route_only"


def test_no_subagents_allows_matching_parent_execution_without_claiming_execution():
    result = route_cli(
        "--no-subagents", "--parent-model", "gpt-6-luna", "--parent-effort", "high",
        *BASE_ARGS,
    )
    assert result["route_model"] == "gpt-6-luna"
    assert result["dispatch_allowed"] is False
    assert result["parent_execution_allowed"] is True
    assert result["dispatch_action"] == "direct_parent_execution_allowed"
    assert result["status"] == "parent_execution_allowed"
    assert result["effective_model"] is None and result["effective_effort"] is None
    assert result["parent_reused"] is False
    assert result["worker_count"] == 0


def test_natural_no_subagents_and_conflicting_explicit_choice():
    natural = route_cli("--user-input", "Do not use subagents", *BASE_ARGS)
    assert natural["subagents_policy"] == "deny"
    assert natural["dispatch_action"] == "blocked_subagent_policy"

    conflict = cli_error(
        "--subagents", "allow", "--user-input", "Do not use subagents", *BASE_ARGS,
    )
    assert conflict.returncode != 0 and "conflicts with natural-language subagents policy" in conflict.stderr
    cli_conflict = cli_error("--no-subagents", "--subagents", "allow", *BASE_ARGS)
    assert cli_conflict.returncode != 0 and "conflicts with --subagents" in cli_conflict.stderr


def test_parent_compatibility_requires_same_model_and_sufficient_effort():
    target = route((1, 2, 2, 2, 0))
    assert module.parent_compatibility("gpt-6-luna", "high", target)["parent_reuse_allowed"]
    assert not module.parent_compatibility("gpt-6-luna", "medium", target)["parent_reuse_allowed"]
    assert not module.parent_compatibility("gpt-6.1-sol", "high", target)["parent_reuse_allowed"]


def test_lightweight_reuse_is_opt_in_and_does_not_claim_execution():
    args = [
        "--clarity", "1", "--scope", "2", "--coupling", "1", "--risk", "1", "--novelty", "1",
        "--parent-model", "gpt-6.1-sol", "--parent-effort", "high",
    ]
    ordinary = route_cli(*args)
    assert ordinary["dispatch_action"] == "delegate_allowed"
    reused = route_cli("--allow-lightweight-reuse", "--file-count", "2", *args)
    assert reused["dispatch_action"] == "direct_parent_execution_allowed"
    assert reused["route_model"] == "gpt-6-luna"
    assert reused["requested_model"] == "gpt-6.1-sol" and reused["requested_effort"] == "high"
    assert reused["effective_model"] is None
    assert reused["parent_execution_allowed"] is True
    assert reused["parent_reused"] is False


def test_lightweight_reuse_keeps_scope_effort_and_high_risk_safeguards():
    target = route((1, 2, 2, 2, 0))
    assert not module.lightweight_reuse_decision(target, "gpt-6.1-sol", "high", enabled=True)["eligible"]
    assert not module.lightweight_reuse_decision(
        target, "gpt-6.1-sol", "medium", enabled=True, file_count=2,
    )["eligible"]
    high_risk = route((2, 3, 3, 2, 1))
    assert high_risk.model == "gpt-6.1-sol"
    assert not module.lightweight_reuse_decision(
        high_risk, "gpt-6.1-sol", "high", enabled=True, file_count=2,
    )["eligible"]


def test_validated_cache_cleanup_remains_explicit():
    args = [
        "--allow-lightweight-reuse", "--validated-cache-cleanup", "--established-command",
        "--reversible-command", "--flag", "cache_cleanup", "--flag", "cache",
        "--flag", "destructive", "--parent-model", "gpt-6-luna", "--parent-effort", "high",
        "--clarity", "1", "--scope", "1", "--coupling", "1", "--risk", "4", "--novelty", "0",
    ]
    result = route_cli(*args)
    assert result["route_model"] == "gpt-6.1-sol" and result["route_effort"] == "high"
    assert result["dispatch_action"] == "direct_parent_execution_allowed"
    assert result["requested_model"] == "gpt-6-luna"

    denied = cli_error(
        "--allow-lightweight-reuse", "--established-command", "--reversible-command",
        "--flag", "cache_cleanup", "--flag", "cache", "--flag", "destructive",
        "--parent-model", "gpt-6-luna", "--parent-effort", "high",
        "--clarity", "1", "--scope", "1", "--coupling", "1", "--risk", "4", "--novelty", "0",
    )
    assert denied.returncode == 0
    assert json.loads(denied.stdout)["dispatch_action"] != "direct_parent_execution_allowed"


def test_delegated_worker_cannot_dispatch_descendant():
    result = route_cli("--delegated-worker", *BASE_ARGS)
    assert result["dispatch_action"] == "child_dispatch_denied"
    assert result["dispatch_allowed"] is False
    assert result["parent_execution_allowed"] is False
    assert result["status"] == "blocked"
    assert result["escalation_required"] is True
    assert result["blocker_kind"] == "delegated_worker_cannot_dispatch"


def test_explicit_model_effort_matrix_and_rejection():
    expected_efforts = {
        "gpt-6-luna": {"none", "low", "medium", "high", "xhigh", "max"},
        "gpt-6.1-sol": {"low", "medium", "high", "xhigh", "max", "ultra"},
        "gpt-6-astra": {"low", "medium", "high", "xhigh", "max", "ultra"},
    }
    assert module.MODEL_EFFORTS == expected_efforts
    for model, efforts in module.MODEL_EFFORTS.items():
        for effort in efforts:
            module.validate_model_effort(model, effort)
    for model, effort in (("gpt-6.1-sol", "none"), ("gpt-6-astra", "none"), ("gpt-6-luna", "invalid")):
        try:
            module.validate_model_effort(model, effort)
        except ValueError:
            pass
        else:
            raise AssertionError(f"unsupported effort accepted for {model}: {effort}")

    exact = route_cli("--explicit-model", "gpt-6.1-sol", "--explicit-effort", "low", *BASE_ARGS)
    assert exact["route_model"] == exact["requested_model"] == "gpt-6.1-sol"
    assert exact["route_effort"] == exact["requested_effort"] == "low"
    assert exact["dispatch_action"] == "delegate_allowed"
    ultra = route_cli("--explicit-model", "gpt-6.1-sol", "--explicit-effort", "ultra", *BASE_ARGS)
    assert ultra["requested_model"] == "gpt-6.1-sol"
    assert ultra["requested_effort"] == "ultra"

    unknown = cli_error("--explicit-model", "gpt-5.6", *BASE_ARGS)
    assert unknown.returncode != 0 and "invalid choice" in unknown.stderr
    unsupported = cli_error("--explicit-model", "gpt-6.1-sol", "--explicit-effort", "none", *BASE_ARGS)
    assert unsupported.returncode != 0 and "unsupported explicit model/effort combination" in unsupported.stderr
    luna_none = route_cli("--explicit-effort", "none", *BASE_ARGS)
    assert luna_none["requested_model"] == "gpt-6-luna" and luna_none["requested_effort"] == "none"


def test_audit_fields_are_truthful_and_attempt_index_counts_prior_failures():
    result = route_cli(
        "--failure-kind", "dependency", "--failure-kind", "reasoning",
        "--failure-kind", "logic", "--failure-kind", "test", *BASE_ARGS,
    )
    assert uuid.UUID(result["decision_id"])
    assert result["route_version"] == "1.5.0"
    assert result["policy_mode"] == "balanced"
    assert result["attempt_index"] == 5
    assert result["failure_kind"] == "test"
    assert result["failure_kinds"] == ["dependency", "reasoning", "logic", "test"]
    assert result["reasoning_escalation_count"] == 2
    assert result["worker_count"] == 0
    assert result["verification_reused"] is False
    assert result["effective_model"] is None and result["effective_effort"] is None


def test_no_availability_preflight_or_fallback_state():
    result = route_cli(*BASE_ARGS)
    assert result["route_model"] == result["requested_model"] == "gpt-6-luna"
    assert result["dispatch_action"] == "delegate_allowed"
    assert not ({
        "availability", "probe_count", "fallback_count", "fallback_reason",
        "availability_state_unchanged",
    } & result.keys())
