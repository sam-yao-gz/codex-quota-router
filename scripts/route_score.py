#!/usr/bin/env python3
"""Deterministic helper for the codex-quota-router skill."""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Route:
    agent: str
    model: str
    effort: str
    score: int
    reason: str


EFFORT_ORDER = {"low": 0, "medium": 1, "high": 2}


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


def choose_route(clarity: int, scope: int, coupling: int, risk: int, novelty: int, failed_attempts: int, flags: set[str]) -> Route:
    bounded("clarity", clarity, 0, 2); bounded("scope", scope, 0, 3); bounded("coupling", coupling, 0, 3)
    bounded("risk", risk, 0, 4); bounded("novelty", novelty, 0, 2); bounded("failed_attempts", failed_attempts, 0, 2)
    score = clarity + scope + coupling + risk + novelty + failed_attempts
    if flags & {"architecture", "multi_system_redesign", "terra_failed"} and (risk >= 3 or coupling >= 3 or failed_attempts >= 1):
        return Route("sol_architect", "gpt-5.6-sol", "medium", score, "architecture/root-cause planning gate; downgrade implementation afterward")
    if flags & {"migration", "auth", "payment", "concurrency", "destructive", "production_incident", "data_loss", "security"}:
        return Route("terra_guard", "gpt-5.6-terra", "high", score, "data, security, concurrency, destructive, or production-risk gate")
    if flags & {"cache", "idempotency", "intermittent", "cross_module_unknown"} or (failed_attempts >= 1 and score >= 8):
        return Route("terra_resolver", "gpt-5.6-terra", "medium", score, "hidden-state/coupling gate or evidence-backed escalation")
    if score <= 2: return Route("luna_fast", "gpt-5.6-luna", "low", score, "mechanical bounded task")
    if score <= 6: return Route("luna_worker", "gpt-5.6-luna", "medium", score, "default clear implementation")
    if score <= 10: return Route("luna_deep", "gpt-5.6-luna", "high", score, "bounded nontrivial task")
    if score <= 13: return Route("terra_resolver", "gpt-5.6-terra", "medium", score, "complexity exceeded Luna threshold")
    return Route("terra_guard", "gpt-5.6-terra", "high", score, "high complexity/risk score")


def apply_luna_availability_fallback(route: Route) -> Route:
    if route.model != "gpt-5.6-luna": return route
    return Route("terra_resolver", "gpt-5.6-terra", "medium", route.score, f"availability fallback from {route.agent}: Luna runtime unavailable; reuse same task packet")


def apply_disable_luna(route: Route) -> Route:
    """Map a Luna route to Terra Medium without consulting availability state."""
    if route.model != "gpt-5.6-luna":
        return route
    return Route(
        "terra_resolver", "gpt-5.6-terra", "medium", route.score,
        f"user override disable_luna from {route.agent}; Luna availability bypassed",
    )


def availability_decision(runtime_dir: str | None, now: int | None, force_probe: bool, probe_lease: int | None = None) -> dict:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from model_availability import DEFAULT_PROBE_LEASE, decide, default_runtime_dir, load_state
    directory = Path(runtime_dir) if runtime_dir else default_runtime_dir()
    state = load_state(directory)
    return {"runtime_dir": str(directory), "state": state, "decision": decide(state, int(time.time()) if now is None else now, force_probe, DEFAULT_PROBE_LEASE if probe_lease is None else probe_lease)}


def dispatch_decision(route: Route, availability: dict | None, luna_unavailable: bool, disable_luna: bool = False, use_luna_only: bool = False) -> tuple[Route, str, str | None]:
    """Keep dispatch action and requested model coherent; transport/inspection never silently fall back."""
    if disable_luna and use_luna_only:
        raise ValueError("conflicting user policies: disable_luna and Use Luna only")
    if disable_luna:
        return apply_disable_luna(route), "user_override", None
    if use_luna_only:
        if route.model != "gpt-5.6-luna":
            return route, "blocked_user_policy", "Use Luna only conflicts with the selected non-Luna risk gate"
        if luna_unavailable or (availability and availability["decision"]["action"] == "use_fallback"):
            return route, "blocked_user_policy", "Use Luna only: Luna cannot be started; no fallback permitted"
    if route.model != "gpt-5.6-luna": return route, "use_luna" if route.model.endswith("luna") else "use_fallback", None
    if luna_unavailable:
        return apply_luna_availability_fallback(route), "use_fallback", "manual/test override: Luna runtime unavailable"
    action = availability["decision"]["action"]
    if action == "use_fallback": return apply_luna_availability_fallback(route), action, availability["decision"]["fallback_reason"]
    # use_luna, probe_luna, and inspect_existing_probe retain the Luna request.
    return route, action, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Score a task for Luna-first Codex routing")
    for name in ("clarity", "scope", "coupling", "risk", "novelty"):
        parser.add_argument("--" + name, type=int, required=True)
    parser.add_argument("--failed-attempts", type=int, default=0); parser.add_argument("--flag", action="append", default=[])
    parser.add_argument("--luna-available", action="store_true"); parser.add_argument("--luna-unavailable", action="store_true")
    parser.add_argument("--disable-luna", action="store_true", help="explicitly bypass Luna availability and route by task risk")
    parser.add_argument("--user-input", "--prompt", help="documented natural-language user policy input")
    parser.add_argument("--runtime-dir"); parser.add_argument("--now", type=int); parser.add_argument("--probe-lease", type=int)
    parser.add_argument("--parent-model"); parser.add_argument("--parent-effort", choices=tuple(EFFORT_ORDER))
    args = parser.parse_args()
    try:
        flags = set(args.flag)
        detected_disable, use_luna_only = detect_user_policy(args.user_input, flags)
        disable_luna = bool(args.disable_luna or detected_disable)
        route = choose_route(args.clarity, args.scope, args.coupling, args.risk, args.novelty, args.failed_attempts, flags)
        # A disable-luna policy must not read or mutate the availability controller.
        availability = None if disable_luna else availability_decision(args.runtime_dir, args.now, args.luna_available, args.probe_lease)
        requested, dispatch_action, fallback_reason = dispatch_decision(route, availability, args.luna_unavailable, disable_luna, use_luna_only)
    except ValueError as exc:
        parser.error(str(exc))
    result = asdict(requested)
    result.update({"route_agent": route.agent, "route_model": route.model, "route_effort": route.effort, "requested_model": requested.model, "requested_effort": requested.effort, "effective_model": None, "effective_effort": None, "dispatch_action": dispatch_action, "fallback_reason": fallback_reason, "availability": availability, "user_override": "disable_luna" if disable_luna else None, "availability_state_unchanged": bool(disable_luna), "probe_count": 0 if disable_luna else None, "fallback_count": 0 if disable_luna else None, **parent_compatibility(args.parent_model, args.parent_effort, requested)})
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
