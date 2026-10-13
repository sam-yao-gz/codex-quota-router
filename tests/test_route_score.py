from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tomllib
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "route_score.py"
spec = importlib.util.spec_from_file_location("route_score", MODULE_PATH)
module = importlib.util.module_from_spec(spec); assert spec and spec.loader
sys.modules[spec.name] = module; spec.loader.exec_module(module)


def route(values, flags=()): return module.choose_route(*values, set(flags)).agent
def route_cli(*args):
    result = subprocess.run([sys.executable, str(MODULE_PATH), *args], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def test_mechanical(): assert route((0, 0, 0, 0, 0, 0)) == "luna_fast"
def test_default_feature(): assert route((0, 1, 1, 1, 0, 0)) == "luna_worker"
def test_bounded_multifile(): assert route((1, 2, 2, 2, 1, 0)) == "luna_deep"
def test_idempotency_gate(): assert route((1, 1, 2, 2, 1, 0), {"idempotency"}) == "sol_resolver"
def test_migration_gate(): assert route((0, 1, 1, 2, 0, 0), {"migration"}) == "sol_guard"
def test_architecture_gate(): assert route((2, 3, 3, 3, 2, 0), {"architecture"}) == "sol_architect"


def test_sensitive_and_unknown_deletion_flags_select_sol_high():
    flags = ("production_change", "credentials", "credential", "secrets", "secret", "unknown_deletion", "recursive_delete", "unknown_recursive_delete")
    for flag in flags:
        selected = module.choose_route(0, 0, 0, 0, 0, 0, {flag})
        assert (selected.agent, selected.model, selected.effort) == ("sol_guard", "gpt-6.1-sol", "high")


def test_profile_models_match_every_active_route():
    cases = [
        ((0, 0, 0, 0, 0, 0), set()),
        ((0, 1, 1, 1, 0, 0), set()),
        ((1, 2, 2, 2, 1, 0), set()),
        ((1, 1, 2, 2, 1, 0), {"idempotency"}),
        ((0, 1, 1, 2, 0, 0), {"migration"}),
        ((2, 3, 3, 3, 2, 0), {"architecture"}),
    ]
    expected = {"gpt-6-luna", "gpt-6.1-sol", "gpt-6-astra"}
    for values, flags in cases:
        selected = module.choose_route(*values, flags)
        profile = MODULE_PATH.parents[1] / "agents" / (selected.agent.replace("_", "-") + ".toml")
        data = tomllib.loads(profile.read_text(encoding="utf-8"))
        assert (data["name"], data["model"], data["model_reasoning_effort"]) == (selected.agent, selected.model, selected.effort)
        assert selected.model in expected


def test_luna_route_has_no_availability_state_or_preflight_fields():
    result = route_cli("--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0")
    assert result["route_model"] == result["requested_model"] == "gpt-6-luna"
    assert result["dispatch_action"] == "use_selected"
    assert not ({"availability", "probe_count", "fallback_count", "fallback_reason", "availability_state_unchanged"} & result.keys())


def test_route_score_runs_when_availability_controller_import_is_blocked():
    guard = """
import builtins, runpy, sys
real_import = builtins.__import__
def deny_controller(name, *args, **kwargs):
    if name == "model_availability":
        raise ImportError("controller intentionally unavailable")
    return real_import(name, *args, **kwargs)
builtins.__import__ = deny_controller
script, *args = sys.argv[1:]
sys.argv = [script, *args]
runpy.run_path(script, run_name="__main__")
"""
    result = subprocess.run([sys.executable, "-c", guard, str(MODULE_PATH), "--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0"], capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)["requested_model"] == "gpt-6-luna"


def test_removed_availability_cli_flags_are_not_accepted():
    help_result = subprocess.run([sys.executable, str(MODULE_PATH), "--help"], capture_output=True, text=True, check=True)
    for old_flag in ("--luna-available", "--luna-unavailable", "--runtime-dir", "--probe-lease"):
        assert old_flag not in help_result.stdout
    invalid = subprocess.run([sys.executable, str(MODULE_PATH), "--luna-unavailable", "--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0"], capture_output=True, text=True)
    assert invalid.returncode != 0 and "unrecognized arguments" in invalid.stderr


def test_parent_same_model_equal_or_higher_effort_reuses_parent():
    target = module.choose_route(1, 2, 2, 2, 1, 0, set())
    assert module.parent_compatibility("gpt-6-luna", "high", target)["parent_reused"]
    assert not module.parent_compatibility("gpt-6-luna", "medium", target)["parent_reused"]


def test_parent_cross_model_never_reuses_without_lightweight_opt_in():
    target = module.choose_route(0, 0, 0, 0, 0, 0, set())
    assert not module.parent_compatibility("gpt-6.1-sol", "high", target)["parent_reused"]


def test_lightweight_reuse_is_opt_in_and_reports_parent_not_recommended_model():
    args = ["--clarity", "1", "--scope", "2", "--coupling", "2", "--risk", "2", "--novelty", "1", "--parent-model", "gpt-6.1-sol", "--parent-effort", "high"]
    legacy = route_cli(*args)
    assert legacy["dispatch_action"] != "direct_parent_reuse"
    reused = route_cli("--allow-lightweight-reuse", "--file-count", "2", *args)
    assert reused["dispatch_action"] == "direct_parent_reuse"
    assert reused["route_model"] == "gpt-6-luna"
    assert reused["requested_model"] == "gpt-6.1-sol" and reused["requested_effort"] == "high"
    assert reused["effective_model"] is None and reused["parent_reused"] is True
    assert "availability" not in reused


def test_lightweight_reuse_requires_bound_scope_and_adequate_effort():
    target = module.choose_route(1, 2, 2, 2, 1, 0, set())
    assert not module.lightweight_reuse_decision(target, "gpt-6.1-sol", "high", enabled=True)["eligible"]
    assert not module.lightweight_reuse_decision(target, "gpt-6.1-sol", "medium", enabled=True, file_count=2)["eligible"]


def test_lightweight_reuse_rejects_score_escalation_and_unsupported_parent():
    sol_route = module.choose_route(2, 3, 3, 2, 1, 0, set())
    assert sol_route.model == "gpt-6.1-sol"
    assert not module.lightweight_reuse_decision(sol_route, "gpt-6.1-sol", "high", enabled=True, file_count=2)["eligible"]
    luna_route = module.choose_route(0, 0, 0, 0, 0, 0, set())
    assert not module.lightweight_reuse_decision(luna_route, "gpt-6-astra", "high", enabled=True, file_count=1)["eligible"]


def test_disable_luna_is_an_explicit_sol_preference_not_availability_state():
    result = route_cli("--disable-luna", "--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0")
    assert result["requested_model"] == "gpt-6.1-sol" and result["requested_effort"] == "medium"
    assert result["dispatch_action"] == "user_override" and result["user_override"] == "disable_luna"
    assert not ({"availability", "probe_count", "fallback_count", "availability_state_unchanged"} & result.keys())


def test_disable_luna_natural_language_input_and_conflict():
    result = route_cli("--user-input", "$codex-quota-router 禁用 Luna：普通任务", "--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0")
    assert result["user_override"] == "disable_luna" and result["requested_model"] == "gpt-6.1-sol"
    conflict = subprocess.run([sys.executable, str(MODULE_PATH), "--user-input", "这次禁用 Luna; Use Luna only", "--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0"], capture_output=True, text=True)
    assert conflict.returncode != 0 and "conflicting user policies" in conflict.stderr


def test_use_luna_only_keeps_luna_route_and_rejects_sol_risk_route():
    luna = route_cli("--flag", "use_luna_only", "--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0")
    assert luna["requested_model"] == "gpt-6-luna" and luna["dispatch_action"] == "use_selected"
    sol = route_cli("--flag", "use_luna_only", "--flag", "migration", "--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0")
    assert sol["requested_model"] == "gpt-6.1-sol" and sol["dispatch_action"] == "blocked_user_policy"


def test_explicit_model_effort_and_disable_luna_preserve_user_choice():
    exact = route_cli("--explicit-model", "gpt-6.1-sol", "--explicit-effort", "low", "--allow-lightweight-reuse", "--file-count", "1", "--parent-model", "gpt-6-luna", "--parent-effort", "high", "--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0")
    assert exact["route_model"] == exact["requested_model"] == "gpt-6.1-sol"
    assert exact["route_effort"] == exact["requested_effort"] == "low"
    assert exact["dispatch_action"] == "use_selected" and exact["parent_reused"] is False
    effort = route_cli("--explicit-effort", "low", "--parent-model", "gpt-6-luna", "--parent-effort", "high", "--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0")
    assert effort["requested_effort"] == "low" and effort["parent_reused"] is False
    sol_high = route_cli("--disable-luna", "--explicit-effort", "high", "--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0")
    assert sol_high["requested_model"] == "gpt-6.1-sol" and sol_high["requested_effort"] == "high"


def test_validated_cache_cleanup_keeps_safeguards_explicit():
    result = route_cli("--allow-lightweight-reuse", "--validated-cache-cleanup", "--established-command", "--reversible-command", "--flag", "cache_cleanup", "--flag", "cache", "--flag", "destructive", "--parent-model", "gpt-6-luna", "--parent-effort", "high", "--clarity", "1", "--scope", "1", "--coupling", "1", "--risk", "4", "--novelty", "0")
    assert result["route_model"] == "gpt-6.1-sol" and result["route_effort"] == "high"
    assert result["dispatch_action"] == "direct_parent_reuse" and result["requested_model"] == "gpt-6-luna"
    denied = route_cli("--allow-lightweight-reuse", "--established-command", "--reversible-command", "--flag", "cache_cleanup", "--flag", "cache", "--flag", "destructive", "--parent-model", "gpt-6-luna", "--parent-effort", "high", "--clarity", "1", "--scope", "1", "--coupling", "1", "--risk", "4", "--novelty", "0")
    assert denied["dispatch_action"] != "direct_parent_reuse"


def test_delegated_worker_cannot_dispatch_descendant_or_reuse_lightweight():
    args = ["--allow-lightweight-reuse", "--file-count", "1", "--parent-model", "gpt-6-luna", "--parent-effort", "high", "--clarity", "0", "--scope", "0", "--coupling", "0", "--risk", "0", "--novelty", "0"]
    result = route_cli("--delegated-worker", *args)
    assert result["dispatch_action"] == "child_dispatch_denied"
    assert result["dispatch_allowed"] is False and result["parent_reused"] is False
    assert result["status"] == "blocked" and result["escalation_required"] is True
