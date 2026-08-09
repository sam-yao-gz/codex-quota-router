#!/usr/bin/env python3
"""Dependency-free Luna availability circuit breaker and dispatch audit."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

DEFAULT_COOLDOWN = 1800
DEFAULT_PROBE_LEASE = 300
SCHEMA_VERSION = 2

MODEL_UNAVAILABLE_MARKERS = (
    "model unavailable", "model is unavailable", "model not available",
    "model unsupported", "model is unsupported", "model not allowed",
    "luna unavailable", "luna is unavailable", "luna unsupported",
    "luna not allowed", "luna quota", "luna capacity",
)
TRANSPORT_TLS_MARKERS = (
    "unknownissuer", "unknown issuer", "sec_e_no_credentials",
    "certificate", "tls", "ssl", "x509", "peer certificate",
)


def classify_error(error: str | None) -> str:
    """Return a non-sensitive class suitable for circuit and audit decisions."""
    text = str(error or "").lower()
    if any(marker in text for marker in TRANSPORT_TLS_MARKERS):
        return "transport_tls"
    if any(marker in text for marker in MODEL_UNAVAILABLE_MARKERS):
        return "model_unavailable"
    return "unknown"


def default_runtime_dir() -> Path:
    return Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".codex" / "runtime" / "codex-quota-router"


def initial_state() -> dict:
    return {"schema_version": SCHEMA_VERSION, "luna": {
        "circuit_state": "closed", "status": "unknown", "failure_count": 0,
        "last_error": None, "last_checked_at": None, "unavailable_until": None,
        "probe_started_at": None,
    }}


@contextmanager
def locked(runtime_dir: Path):
    runtime_dir.mkdir(parents=True, exist_ok=True)
    lock = runtime_dir / ".model_availability.lock"
    deadline = time.monotonic() + 3
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise RuntimeError("availability lock timed out")
            time.sleep(0.02)
    try:
        yield
    finally:
        os.close(fd)
        try:
            lock.unlink()
        except FileNotFoundError:
            pass


def load_state(runtime_dir: Path) -> dict:
    path = runtime_dir / "model_availability.json"
    if not path.exists():
        return initial_state()
    data = json.loads(path.read_text(encoding="utf-8"))
    base = initial_state()
    # v1 state had status=available. Preserve it rather than inferring a new result.
    base["luna"].update(data.get("luna", {}))
    return base


def atomic_json(path: Path, data: dict) -> None:
    fd, temp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(data, out, ensure_ascii=False, sort_keys=True)
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def decide(state: dict, now: int, force_probe: bool = False, probe_lease: int = DEFAULT_PROBE_LEASE) -> dict:
    """Return one unambiguous dispatcher action; this function never selects Terra for a live probe."""
    luna = state["luna"]
    circuit = luna["circuit_state"]
    if circuit == "half_open":
        started = luna.get("probe_started_at")
        if started is None or now >= started + probe_lease:
            return {"allow_luna": False, "action": "probe_luna", "fallback_reason": None, "probe_stale": True}
        return {"allow_luna": False, "action": "inspect_existing_probe", "fallback_reason": None, "probe_stale": False}
    if force_probe or (circuit == "open" and now >= (luna.get("unavailable_until") or 0)):
        return {"allow_luna": False, "action": "probe_luna", "fallback_reason": None, "probe_stale": False}
    if circuit == "open":
        return {"allow_luna": False, "action": "use_fallback", "fallback_reason": "Luna runtime unavailable; cooldown active", "probe_stale": False}
    return {"allow_luna": True, "action": "use_luna", "fallback_reason": None, "probe_stale": False}


def mutate(runtime_dir: Path, now: int, action: str, error: str | None = None, cooldown: int = DEFAULT_COOLDOWN, probe_lease: int = DEFAULT_PROBE_LEASE) -> dict:
    with locked(runtime_dir):
        state = load_state(runtime_dir)
        luna = state["luna"]
        if action == "start-probe":
            choice = decide(state, now, probe_lease=probe_lease)
            if choice["action"] == "probe_luna":
                luna.update(circuit_state="half_open", status="probing", probe_started_at=now, last_checked_at=now)
                atomic_json(runtime_dir / "model_availability.json", state)
            return {"state": state, "decision": choice}
        luna["last_checked_at"] = now
        if action == "unavailable":
            error_kind = classify_error(error)
            if error_kind != "model_unavailable":
                raise ValueError("refusing to open Luna circuit for " + error_kind + "; release the probe and audit the non-availability outcome")
            luna.update(circuit_state="open", status="unavailable", failure_count=luna["failure_count"] + 1, last_error=error or "luna_unavailable", unavailable_until=now + cooldown, probe_started_at=None)
        elif action == "available":
            luna.update(circuit_state="closed", status="available", failure_count=0, last_error=None, unavailable_until=None, probe_started_at=None)
        elif action == "release-probe":
            # Inconclusive, transport, and metadata-unverified results prove neither availability nor unavailability.
            luna.update(circuit_state="closed", status="unknown", last_error=error, unavailable_until=None, probe_started_at=None)
        atomic_json(runtime_dir / "model_availability.json", state)
        return {"state": state}


def audit(runtime_dir: Path, event: str, fields: dict) -> dict:
    required = ("task_packet_id", "route_decision_id", "dispatch_attempt_id")
    missing = [key for key in required if not fields.get(key)]
    if missing:
        raise ValueError("missing audit IDs: " + ", ".join(missing))
    if event == "worker_completed" and not (fields.get("worker_result_nonce") or fields.get("business_result")):
        raise ValueError("worker_completed requires worker_result_nonce or business_result")
    if event == "start_unknown" and (fields.get("worker_result_nonce") or fields.get("business_result")):
        raise ValueError("worker output must be recorded as worker_completed, not start_unknown")
    record = {"event": event, "at": fields.pop("at", int(time.time())), **fields}
    with locked(runtime_dir):
        with (runtime_dir / "dispatch_audit.jsonl").open("a", encoding="utf-8") as out:
            out.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-dir", type=Path, default=default_runtime_dir())
    parser.add_argument("--now", type=int, default=None)
    parser.add_argument("--cooldown", type=int, default=DEFAULT_COOLDOWN)
    parser.add_argument("--probe-lease", type=int, default=DEFAULT_PROBE_LEASE)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("read")
    sub.add_parser("decide").add_argument("--luna-available", action="store_true")
    sub.add_parser("start-probe")
    unavailable = sub.add_parser("unavailable")
    unavailable.add_argument("--error", required=True)
    sub.add_parser("available")
    release = sub.add_parser("release-probe")
    release.add_argument("--error")
    write = sub.add_parser("audit")
    write.add_argument("--event", required=True, choices=("route_decided", "dispatch_requested", "worker_started", "start_rejected", "start_unknown", "effective_model_verified", "metadata_unverified", "worker_completed", "probe_released"))
    for name in ("task-packet-id", "route-decision-id", "dispatch-attempt-id", "parent-model", "route-model", "route-effort", "requested-model", "requested-effort", "effective-model", "effective-effort", "fallback-reason", "status", "worker-result-nonce", "business-result", "parent-reused", "worker-count", "fallback-count", "probe-count", "verification-reused", "reasoning-escalation-count"):
        write.add_argument("--" + name)
    write.add_argument("--error-kind", choices=("model_unavailable", "transport_tls", "environment", "metadata_unverified", "unknown"))
    args = parser.parse_args()
    now = int(time.time()) if args.now is None else args.now
    if args.command == "read":
        state = load_state(args.runtime_dir)
        result = {"state": state, "decision": decide(state, now, probe_lease=args.probe_lease)}
    elif args.command == "decide":
        state = load_state(args.runtime_dir)
        result = {"state": state, "decision": decide(state, now, args.luna_available, args.probe_lease)}
    elif args.command in ("start-probe", "unavailable", "available", "release-probe"):
        result = mutate(args.runtime_dir, now, args.command, getattr(args, "error", None), args.cooldown, args.probe_lease)
    else:
        fields = {key.replace("_", "-").replace("-", "_"): value for key, value in vars(args).items() if key not in {"runtime_dir", "now", "cooldown", "probe_lease", "command", "event"} and value is not None}
        result = audit(args.runtime_dir, args.event, fields)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
