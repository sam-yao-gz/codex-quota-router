# Availability contract

The Skill is an instruction layer. `scripts/model_availability.py` owns the
persistent circuit and JSONL audit, but cannot intercept a runtime that does not
call it. Dispatchers must call `decide`, then `start-probe` when required, and
record lifecycle events.

Runtime defaults are `%USERPROFILE%\\.codex\\runtime\\codex-quota-router\\`,
with `model_availability.json` and `dispatch_audit.jsonl`. The controller takes
`--runtime-dir` and `--now` for isolated deterministic tests. Its writes are
short-lock protected and atomic.

| Circuit | Decision |
|---|---|
| closed | `use_luna` |
| open before cooldown | `use_fallback` / Terra Medium, no Luna request |
| open after cooldown | `probe_luna` with the business task |
| half_open within 300-second lease | `inspect_existing_probe`, never Terra fallback |
| half_open after lease | `probe_luna`; the stale lease is reclaimable |

The initial state is `closed/unknown`; legacy v1 state files remain readable. Record `available` only after a successful probe/runtime start and concrete worker output. Record
`unavailable --error <evidence>` only for explicit model availability errors;
it increments `failure_count`, opens the circuit, and starts a 1800-second
cooldown. The controller classifies certificate/TLS evidence (including
`UnknownIssuer`) as `transport_tls` and rejects it for `unavailable`; record
that outcome as `audit --event start_unknown --error-kind transport_tls` and
inspect the CLI/network path. Unknown and other environment failures likewise
remain `start_unknown` and cannot open the Luna circuit. `--luna-available`
requests a forced probe and never closes a circuit without a later `available`
result.

Every audit event needs `task_packet_id`, `route_decision_id`, and
`dispatch_attempt_id`. It may carry route, requested, effective model/effort,
fallback reason, status, and a non-sensitive `error_kind`
(`model_unavailable`, `transport_tls`, `environment`, or `unknown`).
`start_unknown` is a hold-and-inspect event, not a fallback authorization. TLS/transport failures stop for inspection and never select Terra. For an inconclusive, transport, or metadata-unverified probe outcome, call `release-probe`; it returns to `closed/unknown` so a lease cannot stick forever. Do not manually close a circuit.

`worker_completed` is business evidence: supply `worker_result_nonce` or `business_result`, even if `effective_model` is unavailable. In that case also audit `metadata_unverified`; do not mislabel a completed worker `start_unknown`.

The audit accepts `parent_model`, route/requested/effective model and effort, `parent_reused`, `worker_count`, `fallback_count`, `probe_count`, `verification_reused`, and `reasoning_escalation_count`. They are factual event metadata, not real credit telemetry.
