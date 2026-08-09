from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "model_availability.py"
spec = importlib.util.spec_from_file_location("model_availability", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def runtime() -> Path: return Path(tempfile.mkdtemp())


def test_initial_state_is_unknown_but_closed():
    state = module.initial_state()["luna"]
    assert state["status"] == "unknown" and state["circuit_state"] == "closed"


def test_legacy_state_is_compatible():
    directory = runtime()
    (directory / "model_availability.json").write_text(json.dumps({"schema_version": 1, "luna": {"status": "available", "circuit_state": "closed"}}), encoding="utf-8")
    assert module.load_state(directory)["luna"]["status"] == "available"


def test_closed_allows_luna(): assert module.decide(module.initial_state(), 100)["action"] == "use_luna"


def test_unavailable_opens_and_persists_failure_count():
    directory = runtime(); module.mutate(directory, 100, "unavailable", "Luna model unavailable")
    assert module.load_state(directory)["luna"]["failure_count"] == 1
    module.mutate(directory, 101, "unavailable", "Luna model unavailable")
    assert module.load_state(directory)["luna"]["failure_count"] == 2


def test_open_before_cooldown_uses_fallback():
    directory = runtime(); module.mutate(directory, 100, "unavailable", "Luna model unavailable")
    assert module.decide(module.load_state(directory), 101)["action"] == "use_fallback"


def test_cooldown_requires_luna_probe():
    directory = runtime(); module.mutate(directory, 100, "unavailable", "Luna model unavailable")
    assert module.decide(module.load_state(directory), 1900)["action"] == "probe_luna"
    assert module.mutate(directory, 1900, "start-probe")["state"]["luna"]["circuit_state"] == "half_open"


def test_half_open_inspects_existing_probe_without_fallback():
    directory = runtime(); module.mutate(directory, 100, "unavailable", "Luna model unavailable"); module.mutate(directory, 1900, "start-probe")
    decision = module.decide(module.load_state(directory), 1901)
    assert decision["action"] == "inspect_existing_probe" and decision["fallback_reason"] is None


def test_stale_half_open_is_recoverable_after_default_lease():
    directory = runtime(); module.mutate(directory, 100, "unavailable", "Luna model unavailable"); module.mutate(directory, 1900, "start-probe")
    decision = module.decide(module.load_state(directory), 2200)
    assert decision["action"] == "probe_luna" and decision["probe_stale"]
    module.mutate(directory, 2200, "start-probe")
    assert module.load_state(directory)["luna"]["probe_started_at"] == 2200


def test_probe_success_closes_circuit():
    directory = runtime(); module.mutate(directory, 100, "unavailable", "Luna model unavailable"); module.mutate(directory, 1900, "start-probe"); module.mutate(directory, 1901, "available")
    state = module.load_state(directory)["luna"]
    assert state["circuit_state"] == "closed" and state["failure_count"] == 0


def test_inconclusive_probe_releases_closed_unknown():
    directory = runtime(); module.mutate(directory, 100, "unavailable", "Luna model unavailable"); module.mutate(directory, 1900, "start-probe")
    module.mutate(directory, 1901, "release-probe", "metadata unavailable")
    state = module.load_state(directory)["luna"]
    assert state["circuit_state"] == "closed" and state["status"] == "unknown"


def test_tls_error_cannot_open_luna_circuit():
    directory = runtime()
    try: module.mutate(directory, 100, "unavailable", "invalid peer certificate: UnknownIssuer")
    except ValueError as exc: assert "transport_tls" in str(exc)
    else: assert False
    assert module.load_state(directory)["luna"]["circuit_state"] == "closed"


def test_audit_completed_requires_business_evidence_not_model_metadata():
    fields = {"task_packet_id": "task-1", "route_decision_id": "route-1", "dispatch_attempt_id": "attempt-1"}
    try: module.audit(runtime(), "worker_completed", fields)
    except ValueError as exc: assert "worker_result_nonce" in str(exc)
    else: assert False
    record = module.audit(runtime(), "worker_completed", {**fields, "worker_result_nonce": "nonce-1"})
    assert record["event"] == "worker_completed" and "effective_model" not in record


def test_worker_output_cannot_be_misclassified_as_start_unknown():
    fields = {"task_packet_id": "task-1", "route_decision_id": "route-1", "dispatch_attempt_id": "attempt-1", "business_result": "tests passed"}
    try: module.audit(runtime(), "start_unknown", fields)
    except ValueError as exc: assert "worker_completed" in str(exc)
    else: assert False


def test_audit_includes_quota_first_fields():
    fields = {"task_packet_id": "task-1", "route_decision_id": "route-1", "dispatch_attempt_id": "attempt-1", "parent_model": "gpt-5.6-luna", "route_model": "gpt-5.6-luna", "requested_model": "gpt-5.6-luna", "parent_reused": "true", "worker_count": "1", "fallback_count": "0", "probe_count": "1", "verification_reused": "true", "reasoning_escalation_count": "0"}
    record = module.audit(runtime(), "worker_started", fields)
    assert record["verification_reused"] == "true" and record["worker_count"] == "1"
