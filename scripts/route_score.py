#!/usr/bin/env python3
"""Deterministic helper for the codex-quota-router skill."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Route:
    agent: str
    model: str
    effort: str
    score: int
    reason: str


EFFORT_ORDER = {"low": 0, "medium": 1, "high": 2}
LIGHTWEIGHT_PARENT_MODELS = {"gpt-6-luna", "gpt-6.1-sol"}
EXECUTABLE_DISPATCH_ACTIONS = {
    "direct_parent_reuse", "use_selected", "user_override",
}


def detect_user_policy(user_input: str | None, flags: set[str] | None = None) -> tuple[bool, bool]:
    """Return (disable_luna, use_luna_only) from explicit user wording."""
    text = (user_input or "").strip().lower()
    normalized = re.sub(r"[\s_-]+", " ", text)
    flag_text = " ".join(re.sub(r"[\s_-]+", " ", str(flag).strip().lower()) for flag in (flags or set()))
    combined = f"{normalized} {flag_text}"
    disable = bool(re.search(r"禁用\s*luna", text, re.I) or "disable luna" in combined)
    luna_only = bool("use luna only" in combined or "use luna only".replace(" ", "_") in combined)
    if disable and luna_only:
        raise ValueError("conflicting user policies: disable_luna and Use Luna only")
    return disable, luna_only


def bounded(name: str, value: int, low: int, high: int) -> int:
    if not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}, got {value}")
    return value


def parent_compatibility(parent_model: str | None, parent_effort: str | None, target: Route) -> dict:
    """Pure compatibility decision: same model and equal-or-higher effort may reuse the parent."""
    same_model = parent_model == target.model
    valid_effort = parent_effort in EFFORT_ORDER
    target_effort = EFFORT_ORDER[target.effort]
    reuse_parent = bool(same_model and valid_effort and EFFORT_ORDER[parent_effort] >= target_effort)
    return {"parent_model": parent_model, "parent_effort": parent_effort, "same_model": same_model, "parent_reused": reuse_parent}


def lightweight_reuse_decision(
    target: Route, parent_model: str | None, parent_effort: str | None, *,
    enabled: bool = False, file_count: int | None = None,
    established_command: bool = False, read_only: bool = False,
    reversible: bool = False, explicit_override: bool = False,
    use_luna_only: bool = False, risk: int = 0, flags: set[str] | None = None,
    validated_cache_cleanup: bool = False, delegated_worker: bool = False,
) -> dict:
    """Opt-in direct reuse for tiny bounded work; never changes route recommendation."""
    flags = flags or set()
    effort_ok = parent_effort in EFFORT_ORDER and EFFORT_ORDER[parent_effort] >= EFFORT_ORDER[target.effort]
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
        and not use_luna_only and not delegated_worker and not hard_risk
        and (risk <= 2 or cleanup_ok)
        and ("destructive" not in flags or cleanup_ok)
    )
    reason = None
    if not enabled: reason = "lightweight reuse is opt-in"
    elif not parent_ok: reason = "parent model is outside supported GPT-6 Luna/Sol profiles"
    elif not route_ok: reason = "lightweight reuse is limited to Luna routes and validated cache cleanup"
    elif not effort_ok: reason = "parent effort is below the selected route"
    elif not scope_ok: reason = "task is not explicitly bounded to two files or one established safe command"
    elif explicit_override or use_luna_only: reason = "explicit model/effort or Luna-only policy forbids lightweight reuse"
    elif delegated_worker: reason = "delegated workers cannot dispatch or reuse descendants"
    elif hard_risk or (risk > 2 and not cleanup_ok) or ("destructive" in flags and not cleanup_ok): reason = "task has a hard risk gate"
    return {"eligible": eligible, "reason": reason}


def child_dispatch_decision(delegated_worker: bool = False, allow_descendant: bool = False) -> dict:
    """Guard descendant dispatch from a delegated worker.

    Top-level routing remains available. A worker that needs deeper delegation
    must return the blocked result to its parent for escalation instead of
    creating an overlapping descendant worker.
    """
    if delegated_worker and not allow_descendant:
        return {
            "dispatch_allowed": False,
            "dispatch_action": "child_dispatch_denied",
            "status": "blocked",
            "escalation_required": True,
            "reason": "delegated workers must complete the assigned packet in their own thread; report deeper delegation to the parent",
        }
    return {
        "dispatch_allowed": True,
        "dispatch_action": "dispatch_requested",
        "status": "dispatch_requested",
        "escalation_required": False,
        "reason": None,
    }


# Descriptive alias for callers that refer to the boundary as nested dispatch.
nested_dispatch_decision = child_dispatch_decision


def choose_route(clarity: int, scope: int, coupling: int, risk: int, novelty: int, failed_attempts: int, flags: set[str]) -> Route:
    bounded("clarity", clarity, 0, 2); bounded("scope", scope, 0, 3); bounded("coupling", coupling, 0, 3)
    bounded("risk", risk, 0, 4); bounded("novelty", novelty, 0, 2); bounded("failed_attempts", failed_attempts, 0, 2)
    score = clarity + scope + coupling + risk + novelty + failed_attempts
    if flags & {"architecture", "multi_system_redesign", "resolver_failed"} and (risk >= 3 or coupling >= 3 or failed_attempts >= 1):
        return Route("sol_architect", "gpt-6-astra", "medium", score, "architecture/root-cause planning gate; downgrade implementation afterward")
    if flags & {
        "migration", "auth", "payment", "concurrency", "destructive", "production_incident",
        "production_change", "credentials", "credential", "secrets", "secret", "data_loss", "security",
        "unknown_deletion", "recursive_delete", "unknown_recursive_delete",
    }:
        return Route("sol_guard", "gpt-6.1-sol", "high", score, "data, security, concurrency, destructive, or production-risk gate")
    if flags & {"cache", "idempotency", "intermittent", "cross_module_unknown"} or (failed_attempts >= 1 and score >= 8):
        return Route("sol_resolver", "gpt-6.1-sol", "medium", score, "hidden-state/coupling gate or evidence-backed escalation")
    if score <= 2: return Route("luna_fast", "gpt-6-luna", "low", score, "mechanical bounded task")
    if score <= 6: return Route("luna_worker", "gpt-6-luna", "medium", score, "default clear implementation")
    if score <= 10: return Route("luna_deep", "gpt-6-luna", "high", score, "bounded nontrivial task")
    if score <= 13: return Route("sol_resolver", "gpt-6.1-sol", "medium", score, "complexity exceeded Luna threshold")
    return Route("sol_guard", "gpt-6.1-sol", "high", score, "high complexity/risk score")


def apply_disable_luna(route: Route, effort: str | None = None) -> Route:
    """Honor the user's explicit preference for Sol on ordinary Luna routes."""
    if route.model != "gpt-6-luna":
        return route
    return Route(
        "sol_resolver", "gpt-6.1-sol", effort or "medium", route.score,
        f"user override disable_luna from {route.agent}",
    )


def apply_explicit_route(route: Route, model: str | None, effort: str | None) -> Route:
    """Preserve caller-specified model/effort instead of treating them as hints."""
    if model is None and effort is None:
        return route
    selected_model = model or route.model
    selected_effort = effort or route.effort
    return Route("explicit_user_route", selected_model, selected_effort, route.score,
                 "explicit user model/effort override")


def dispatch_decision(route: Route, disable_luna: bool = False, use_luna_only: bool = False, *, delegated_worker: bool = False, worker_context: bool | None = None, allow_descendant: bool = False, disable_luna_effort: str | None = None) -> tuple[Route, str, str | None]:
    """Select the chosen route or report a policy conflict; execution failures are handled by the caller."""
    if worker_context is not None:
        delegated_worker = worker_context
    child_guard = child_dispatch_decision(delegated_worker, allow_descendant)
    if not child_guard["dispatch_allowed"]:
        return route, child_guard["dispatch_action"], child_guard["reason"]
    if disable_luna and use_luna_only:
        raise ValueError("conflicting user policies: disable_luna and Use Luna only")
    if disable_luna:
        return apply_disable_luna(route, disable_luna_effort), "user_override", None
    if use_luna_only:
        if route.model != "gpt-6-luna":
            return route, "blocked_user_policy", "Use Luna only conflicts with the selected non-Luna risk gate"
    return route, "use_selected", None


def main() -> int:
    parser = argparse.ArgumentParser(description="Score a task for Luna-first Codex routing")
    for name in ("clarity", "scope", "coupling", "risk", "novelty"):
        parser.add_argument("--" + name, type=int, required=True)
    parser.add_argument("--failed-attempts", type=int, default=0); parser.add_argument("--flag", action="append", default=[])
    parser.add_argument("--disable-luna", action="store_true", help="explicitly prefer Sol for ordinary Luna routes")
    parser.add_argument("--user-input", "--prompt", help="documented natural-language user policy input")
    parser.add_argument("--parent-model"); parser.add_argument("--parent-effort", choices=tuple(EFFORT_ORDER))
    parser.add_argument("--allow-lightweight-reuse", action="store_true", help="opt into guarded direct reuse by the current parent")
    parser.add_argument("--file-count", type=int, help="known maximum changed-file count for lightweight eligibility")
    parser.add_argument("--established-command", action="store_true")
    parser.add_argument("--read-only-command", action="store_true")
    parser.add_argument("--reversible-command", action="store_true")
    parser.add_argument("--explicit-model", help="explicit model request disables lightweight reuse")
    parser.add_argument("--explicit-effort", choices=tuple(EFFORT_ORDER), help="explicit effort request disables lightweight reuse")
    parser.add_argument("--validated-cache-cleanup", action="store_true", help="assert authorized whitelist cleanup, no reparse traversal, locked files skipped")
    parser.add_argument("--delegated-worker", "--worker-context", dest="delegated_worker", action="store_true", help="deny descendant dispatch from a delegated worker")
    args = parser.parse_args()
    try:
        flags = set(args.flag)
        detected_disable, use_luna_only = detect_user_policy(args.user_input, flags)
        disable_luna = bool(args.disable_luna or detected_disable)
        route = choose_route(args.clarity, args.scope, args.coupling, args.risk, args.novelty, args.failed_attempts, flags)
        if args.explicit_model and disable_luna and args.explicit_model == "gpt-6-luna":
            raise ValueError("explicit Luna model conflicts with disable_luna")
        route = apply_explicit_route(route, args.explicit_model, args.explicit_effort)
        reuse = lightweight_reuse_decision(
            route, args.parent_model, args.parent_effort,
            enabled=args.allow_lightweight_reuse, file_count=args.file_count,
            established_command=args.established_command, read_only=args.read_only_command,
            reversible=args.reversible_command,
            explicit_override=bool(args.explicit_model or args.explicit_effort or disable_luna),
            use_luna_only=use_luna_only, risk=args.risk, flags=flags,
            validated_cache_cleanup=args.validated_cache_cleanup,
            delegated_worker=args.delegated_worker,
        )
        if reuse["eligible"]:
            requested = Route("parent_reuse", args.parent_model, args.parent_effort, route.score,
                              "bounded lightweight reuse; route remains recommendation only")
            dispatch_action, dispatch_reason = "direct_parent_reuse", None
        else:
            requested = None
        child_guard = child_dispatch_decision(args.delegated_worker)
        if requested is None:
            requested, dispatch_action, dispatch_reason = dispatch_decision(route, disable_luna, use_luna_only, delegated_worker=args.delegated_worker, disable_luna_effort=args.explicit_effort)
            expected_model, expected_effort = route.model, route.effort
            if disable_luna and route.model == "gpt-6-luna":
                expected_model, expected_effort = "gpt-6.1-sol", args.explicit_effort or "medium"
            if (args.explicit_model or args.explicit_effort) and (requested.model != expected_model or requested.effort != expected_effort):
                requested, dispatch_action, dispatch_reason = route, "blocked_user_policy", "explicit model/effort prevents user-policy remapping"
    except ValueError as exc:
        parser.error(str(exc))
    result = asdict(requested)
    child_guard = child_dispatch_decision(args.delegated_worker)
    compatibility = parent_compatibility(args.parent_model, args.parent_effort, requested)
    if args.explicit_effort and args.parent_effort != args.explicit_effort:
        compatibility["parent_reused"] = False
    if dispatch_action not in EXECUTABLE_DISPATCH_ACTIONS:
        compatibility["parent_reused"] = False
    if dispatch_action == "direct_parent_reuse":
        compatibility["parent_reused"] = True
    result.update({"route_agent": route.agent, "route_model": route.model, "route_effort": route.effort, "requested_model": requested.model, "requested_effort": requested.effort, "effective_model": None, "effective_effort": None, "dispatch_action": dispatch_action, "dispatch_reason": dispatch_reason, "user_override": "disable_luna" if disable_luna else None, "dispatch_allowed": child_guard["dispatch_allowed"], "status": child_guard["status"] if not child_guard["dispatch_allowed"] else ("parent_reused" if reuse["eligible"] else "route_decided"), "escalation_required": child_guard["escalation_required"], "lightweight_reuse": reuse, **compatibility, "parent_reused": bool(reuse["eligible"] or compatibility["parent_reused"])})
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
