#!/usr/bin/env python3
"""Deterministic helper for the codex-quota-router skill."""
from __future__ import annotations

import argparse
import json
import re
import uuid
from dataclasses import asdict, dataclass
from typing import Sequence


ROUTE_VERSION = "1.5.0"
MODEL_EFFORTS = {
    "gpt-6-luna": {"none", "low", "medium", "high", "xhigh", "max"},
    "gpt-6.1-sol": {"low", "medium", "high", "xhigh", "max", "ultra"},
    "gpt-6-astra": {"low", "medium", "high", "xhigh", "max", "ultra"},
}
EFFORT_ORDER = {"none": -1, "low": 0, "medium": 1, "high": 2, "xhigh": 3, "max": 4, "ultra": 5}
EFFORT_CHOICES = tuple(EFFORT_ORDER)
FAILURE_KINDS = {"reasoning", "logic", "dependency", "permission", "test", "network", "user_input"}
ESCALATING_FAILURE_KINDS = {"reasoning", "logic"}
POLICY_MODES = {"balanced", "quality_first", "route_only"}
SUBAGENT_POLICIES = {"auto", "allow", "deny"}
KNOWN_FLAGS = {
    "architecture", "multi_system_redesign", "resolver_failed",
    "migration", "auth", "payment", "concurrency", "destructive",
    "production_incident", "production_change", "credentials", "credential",
    "secrets", "secret", "data_loss", "security", "unknown_deletion",
    "recursive_delete", "unknown_recursive_delete", "cache", "idempotency",
    "intermittent", "cross_module_unknown", "cache_cleanup",
}
SOL_HIGH_FLAGS = {
    "migration", "auth", "payment", "concurrency", "destructive",
    "production_incident", "production_change", "credentials", "credential",
    "secrets", "secret", "data_loss", "security", "unknown_deletion",
    "recursive_delete", "unknown_recursive_delete",
}
LIGHTWEIGHT_PARENT_MODELS = {"gpt-6-luna", "gpt-6.1-sol"}


@dataclass(frozen=True)
class Route:
    agent: str
    model: str
    effort: str
    score: int
    reason: str


def detect_user_preferences(user_input: str | None) -> dict[str, str]:
    """Read only the three supported natural-language policy controls."""
    text = (user_input or "").lower()
    matches = {
        "quality_first": bool(re.search(r"\bdo\s+not\s+optimize\s+quota\b", text)),
        "route_only": bool(re.search(r"\broute\s+only\b", text)),
        "deny_subagents": bool(re.search(r"\bdo\s+not\s+use\s+subagents\b", text)),
    }
    policies = [name for name in ("quality_first", "route_only") if matches[name]]
    if len(policies) > 1:
        raise ValueError("conflicting natural-language policy choices: quality_first and route_only")
    result: dict[str, str] = {}
    if policies:
        result["policy"] = policies[0]
    if matches["deny_subagents"]:
        result["subagents"] = "deny"
    return result


def bounded(name: str, value: int, low: int, high: int) -> int:
    if not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}, got {value}")
    return value


def validate_model_effort(model: str, effort: str, label: str = "model/effort") -> None:
    if model not in MODEL_EFFORTS:
        raise ValueError(f"unsupported {label} model: {model}")
    if effort not in MODEL_EFFORTS[model]:
        supported = ", ".join(sorted(MODEL_EFFORTS[model], key=EFFORT_ORDER.get))
        raise ValueError(f"unsupported {label} combination: {model} with {effort}; supported efforts: {supported}")


def parent_compatibility(parent_model: str | None, parent_effort: str | None, target: Route) -> dict:
    """A parent can run a route when its model matches and effort is adequate."""
    same_model = parent_model == target.model
    valid_effort = bool(
        parent_model in MODEL_EFFORTS
        and parent_effort in MODEL_EFFORTS[parent_model]
    )
    target_effort = EFFORT_ORDER[target.effort]
    reuse_parent = bool(
        same_model and valid_effort
        and EFFORT_ORDER[parent_effort] >= target_effort
    )
    return {
        "parent_model": parent_model,
        "parent_effort": parent_effort,
        "same_model": same_model,
        "parent_reuse_allowed": reuse_parent,
    }


def lightweight_reuse_decision(
    target: Route, parent_model: str | None, parent_effort: str | None, *,
    enabled: bool = False, file_count: int | None = None,
    established_command: bool = False, read_only: bool = False,
    reversible: bool = False, explicit_override: bool = False,
    risk: int = 0, flags: set[str] | None = None,
    validated_cache_cleanup: bool = False, delegated_worker: bool = False,
) -> dict:
    """Opt-in direct parent execution permission; never changes the route recommendation."""
    flags = flags or set()
    effort_ok = bool(
        parent_model in MODEL_EFFORTS
        and parent_effort in MODEL_EFFORTS[parent_model]
        and parent_effort in EFFORT_ORDER
        and EFFORT_ORDER[parent_effort] >= EFFORT_ORDER[target.effort]
    )
    scope_ok = (file_count is not None and 0 <= file_count <= 2) or (
        established_command and (read_only or reversible)
    )
    cleanup_ok = validated_cache_cleanup and {"cache_cleanup", "cache", "destructive"} <= flags and established_command
    route_ok = target.model == "gpt-6-luna" or (
        cleanup_ok and target.model == "gpt-6.1-sol" and target.effort == "high"
    )
    parent_ok = parent_model in LIGHTWEIGHT_PARENT_MODELS
    hard_risk = flags & {
        "migration", "auth", "payment", "concurrency", "production_incident",
        "production_change", "credentials", "credential", "secrets", "secret",
        "data_loss", "security", "architecture", "multi_system_redesign",
        "resolver_failed", "cache", "idempotency", "intermittent", "cross_module_unknown",
        "unknown_deletion", "recursive_delete", "unknown_recursive_delete",
    }
    if cleanup_ok:
        hard_risk -= {"cache"}
    eligible = bool(
        enabled and parent_ok and route_ok and effort_ok and scope_ok and not explicit_override
        and not delegated_worker and not hard_risk
        and (risk <= 2 or cleanup_ok)
        and ("destructive" not in flags or cleanup_ok)
    )
    reason = None
    if not enabled:
        reason = "lightweight reuse is opt-in"
    elif not parent_ok:
        reason = "parent model is outside supported GPT-6 Luna/Sol profiles"
    elif not route_ok:
        reason = "lightweight reuse is limited to Luna routes and validated cache cleanup"
    elif not effort_ok:
        reason = "parent effort is below the selected route or unsupported for its model"
    elif not scope_ok:
        reason = "task is not explicitly bounded to two files or one established safe command"
    elif explicit_override:
        reason = "explicit model/effort request forbids lightweight reuse"
    elif delegated_worker:
        reason = "delegated workers cannot dispatch or reuse descendants"
    elif hard_risk or (risk > 2 and not cleanup_ok) or ("destructive" in flags and not cleanup_ok):
        reason = "task has a hard risk gate"
    return {"eligible": eligible, "reason": reason}


def child_dispatch_decision(delegated_worker: bool = False, allow_descendant: bool = False) -> dict:
    """Prevent a delegated worker from dispatching descendants by default."""
    if delegated_worker and not allow_descendant:
        return {
            "dispatch_allowed": False,
            "dispatch_action": "child_dispatch_denied",
            "status": "blocked",
            "escalation_required": True,
            "blocker_kind": "delegated_worker_cannot_dispatch",
            "reason": "delegated workers must complete the assigned packet in their own thread; report deeper delegation to the parent",
        }
    return {
        "dispatch_allowed": True,
        "dispatch_action": "delegate_allowed",
        "status": "route_decided",
        "escalation_required": False,
        "blocker_kind": None,
        "reason": None,
    }


nested_dispatch_decision = child_dispatch_decision


def choose_route(
    clarity: int, scope: int, coupling: int, risk: int, novelty: int,
    failure_kinds: Sequence[str], flags: set[str],
) -> Route:
    bounded("clarity", clarity, 0, 2)
    bounded("scope", scope, 0, 3)
    bounded("coupling", coupling, 0, 3)
    bounded("risk", risk, 0, 4)
    bounded("novelty", novelty, 0, 2)
    unknown_flags = flags - KNOWN_FLAGS
    if unknown_flags:
        raise ValueError(f"unknown flags: {', '.join(sorted(unknown_flags))}")
    unknown_failures = set(failure_kinds) - FAILURE_KINDS
    if unknown_failures:
        raise ValueError(f"unknown failure kinds: {', '.join(sorted(unknown_failures))}")

    escalation_count = sum(kind in ESCALATING_FAILURE_KINDS for kind in failure_kinds)
    score = clarity + scope + coupling + risk + novelty + min(escalation_count, 2)

    if flags & SOL_HIGH_FLAGS:
        return Route("sol_guard", "gpt-6.1-sol", "high", score, "data, security, concurrency, destructive, or production-risk gate")
    if flags & {"architecture", "multi_system_redesign", "resolver_failed"} and (
        risk >= 3 or coupling >= 3 or escalation_count >= 1
    ):
        return Route("sol_architect", "gpt-6-astra", "medium", score, "architecture/root-cause planning gate; downgrade implementation afterward")
    if flags & {"cache", "idempotency", "intermittent", "cross_module_unknown"} or (
        escalation_count >= 1 and score >= 8
    ):
        return Route("sol_resolver", "gpt-6.1-sol", "medium", score, "hidden-state/coupling gate or evidence-backed reasoning escalation")
    if score <= 2:
        return Route("luna_fast", "gpt-6-luna", "low", score, "mechanical bounded task")
    if score <= 6:
        return Route("luna_worker", "gpt-6-luna", "medium", score, "default clear implementation")
    if score <= 10:
        return Route("luna_deep", "gpt-6-luna", "high", score, "bounded nontrivial task")
    if score <= 13:
        return Route("sol_resolver", "gpt-6.1-sol", "medium", score, "complexity exceeded Luna threshold")
    return Route("sol_guard", "gpt-6.1-sol", "high", score, "high complexity/risk score")


def apply_quality_first(route: Route) -> Route:
    """Raise ordinary routes one effort step while preserving Astra and Sol High gates."""
    upgrades = {
        ("gpt-6-luna", "low"): ("luna_worker", "gpt-6-luna", "medium"),
        ("gpt-6-luna", "medium"): ("luna_deep", "gpt-6-luna", "high"),
        ("gpt-6-luna", "high"): ("sol_resolver", "gpt-6.1-sol", "medium"),
        ("gpt-6.1-sol", "medium"): ("sol_guard", "gpt-6.1-sol", "high"),
    }
    selected = upgrades.get((route.model, route.effort))
    if selected is None:
        return route
    agent, model, effort = selected
    return Route(
        agent, model, effort, route.score,
        f"quality_first policy promoted {route.model} {route.effort} to {model} {effort}",
    )


def apply_explicit_route(
    route: Route, model: str | None, effort: str | None, *, hard_risk: bool = False,
) -> Route:
    """Preserve explicit model/effort requests and reject unsupported combinations."""
    if model is None and effort is None:
        return route
    selected_model = model or route.model
    selected_effort = effort or route.effort
    validate_model_effort(selected_model, selected_effort, "explicit model/effort")
    if hard_risk and (selected_model != "gpt-6.1-sol" or selected_effort != "high"):
        raise ValueError("explicit model/effort conflicts with Sol High hard-risk gate")
    return Route(
        "explicit_user_route", selected_model, selected_effort, route.score,
        "explicit user model/effort override",
    )


def resolve_policies(
    user_input: str | None, policy: str | None, subagents: str | None, no_subagents: bool,
) -> tuple[str, str]:
    preferences = detect_user_preferences(user_input)
    if policy is not None and policy not in POLICY_MODES:
        raise ValueError(f"unsupported policy: {policy}")
    if subagents is not None and subagents not in SUBAGENT_POLICIES:
        raise ValueError(f"unsupported subagents policy: {subagents}")
    if no_subagents and subagents not in (None, "deny"):
        raise ValueError("--no-subagents conflicts with --subagents other than deny")
    explicit_subagents = "deny" if no_subagents else subagents
    detected_policy = preferences.get("policy")
    if detected_policy and policy and detected_policy != policy:
        raise ValueError(f"--policy {policy} conflicts with natural-language policy {detected_policy}")
    detected_subagents = preferences.get("subagents")
    if detected_subagents and explicit_subagents and detected_subagents != explicit_subagents:
        raise ValueError(
            f"--subagents {explicit_subagents} conflicts with natural-language subagents policy {detected_subagents}"
        )
    return policy or detected_policy or "balanced", explicit_subagents or detected_subagents or "auto"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score a task for Codex model routing")
    for name in ("clarity", "scope", "coupling", "risk", "novelty"):
        parser.add_argument("--" + name, type=int, required=True)
    parser.add_argument("--failure-kind", action="append", choices=sorted(FAILURE_KINDS), default=[])
    parser.add_argument("--flag", action="append", choices=sorted(KNOWN_FLAGS), default=[])
    parser.add_argument("--policy", choices=sorted(POLICY_MODES))
    parser.add_argument("--subagents", choices=sorted(SUBAGENT_POLICIES))
    parser.add_argument("--no-subagents", action="store_true")
    parser.add_argument("--user-input", "--prompt", help="natural-language policy input")
    parser.add_argument("--parent-model")
    parser.add_argument("--parent-effort", choices=EFFORT_CHOICES)
    parser.add_argument("--allow-lightweight-reuse", action="store_true", help="opt into guarded direct parent execution")
    parser.add_argument("--file-count", type=int, help="known maximum changed-file count for lightweight eligibility")
    parser.add_argument("--established-command", action="store_true")
    parser.add_argument("--read-only-command", action="store_true")
    parser.add_argument("--reversible-command", action="store_true")
    parser.add_argument("--explicit-model", choices=sorted(MODEL_EFFORTS), help="explicit model request disables lightweight reuse")
    parser.add_argument("--explicit-effort", choices=EFFORT_CHOICES, help="explicit effort request disables lightweight reuse")
    parser.add_argument("--validated-cache-cleanup", action="store_true", help="assert authorized whitelist cleanup, no reparse traversal, locked files skipped")
    parser.add_argument("--delegated-worker", "--worker-context", dest="delegated_worker", action="store_true", help="deny descendant dispatch from a delegated worker")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    flags = set(args.flag)
    failure_kinds = list(args.failure_kind)
    try:
        policy_mode, subagents_policy = resolve_policies(
            args.user_input, args.policy, args.subagents, args.no_subagents,
        )
        route = choose_route(
            args.clarity, args.scope, args.coupling, args.risk, args.novelty,
            failure_kinds, flags,
        )
        if policy_mode == "quality_first":
            route = apply_quality_first(route)
        route = apply_explicit_route(
            route, args.explicit_model, args.explicit_effort,
            hard_risk=bool(flags & SOL_HIGH_FLAGS),
        )
    except ValueError as exc:
        parser.error(str(exc))

    compatibility = parent_compatibility(args.parent_model, args.parent_effort, route)
    if args.explicit_effort and args.parent_effort != args.explicit_effort:
        compatibility["parent_reuse_allowed"] = False
    reuse = lightweight_reuse_decision(
        route, args.parent_model, args.parent_effort,
        enabled=args.allow_lightweight_reuse,
        file_count=args.file_count,
        established_command=args.established_command,
        read_only=args.read_only_command,
        reversible=args.reversible_command,
        explicit_override=bool(args.explicit_model or args.explicit_effort),
        risk=args.risk,
        flags=flags,
        validated_cache_cleanup=args.validated_cache_cleanup,
        delegated_worker=args.delegated_worker,
    )
    child_guard = child_dispatch_decision(args.delegated_worker)

    requested = route
    dispatch_action = "delegate_allowed"
    dispatch_reason = None
    blocker_kind = None
    status = "route_decided"
    parent_execution_allowed = False
    dispatch_allowed = subagents_policy != "deny" and policy_mode != "route_only"

    if child_guard["status"] == "blocked":
        dispatch_action = child_guard["dispatch_action"]
        dispatch_reason = child_guard["reason"]
        blocker_kind = child_guard["blocker_kind"]
        status = "blocked"
        dispatch_allowed = False
    elif policy_mode == "route_only":
        dispatch_action = "route_only"
        dispatch_reason = "route_only policy reports a recommendation without permitting dispatch"
        blocker_kind = "route_only_policy"
        status = "route_only"
        dispatch_allowed = False
    elif subagents_policy == "deny":
        if compatibility["parent_reuse_allowed"]:
            dispatch_action = "direct_parent_execution_allowed"
            dispatch_reason = "subagents are denied; the current parent matches the route and has adequate effort"
            status = "parent_execution_allowed"
            parent_execution_allowed = True
        else:
            dispatch_action = "blocked_subagent_policy"
            dispatch_reason = "subagents are denied and the current parent does not match the route with adequate effort"
            blocker_kind = "subagents_denied_parent_mismatch"
            status = "route_only"
            dispatch_allowed = False
    elif reuse["eligible"]:
        requested = Route(
            "parent_execution", args.parent_model, args.parent_effort, route.score,
            "bounded lightweight parent execution permitted; route remains recommendation only",
        )
        dispatch_action = "direct_parent_execution_allowed"
        dispatch_reason = None
        parent_execution_allowed = True
        status = "parent_execution_allowed"

    reasoning_escalation_count = sum(kind in ESCALATING_FAILURE_KINDS for kind in failure_kinds)
    result = asdict(requested)
    result.update({
        "decision_id": str(uuid.uuid4()),
        "route_version": ROUTE_VERSION,
        "policy_mode": policy_mode,
        "subagents_policy": subagents_policy,
        "route_agent": route.agent,
        "route_model": route.model,
        "route_effort": route.effort,
        "requested_model": requested.model,
        "requested_effort": requested.effort,
        "effective_model": None,
        "effective_effort": None,
        "dispatch_action": dispatch_action,
        "dispatch_reason": dispatch_reason,
        "dispatch_allowed": bool(dispatch_allowed and child_guard["dispatch_allowed"]),
        "parent_execution_allowed": parent_execution_allowed,
        "parent_reused": False,
        "status": status,
        "escalation_required": child_guard["escalation_required"],
        "lightweight_reuse": reuse,
        "blocker_kind": blocker_kind,
        "attempt_index": len(failure_kinds) + 1,
        "failure_kind": failure_kinds[-1] if failure_kinds else None,
        "failure_kinds": failure_kinds,
        "worker_count": 0,
        "reasoning_escalation_count": reasoning_escalation_count,
        "verification_reused": False,
        **compatibility,
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
