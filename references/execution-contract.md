# Execution contract

This file closes the gap between **route selection** and **actual model execution**.

## Core invariant

A routing label is not proof of execution.

If the parent thread is not running the selected model, substantive work must be delegated before the parent continues. For the same model, a parent with equal or higher reasoning effort may set `parent_reused=true`; lower effort must delegate.

## State machine

```text
route_decided
-> task_packet_built
-> dispatch_requested
-> worker_started
-> effective_model_verified (when runtime evidence is accessible)
-> worker_completed
```

`start_rejected` and `start_unknown` are not interchangeable. Only an explicit
`start_rejected` caused by a Luna availability error may open the circuit and
trigger Terra Medium. For `start_unknown`, inspect the child agent/session first;
do not start Terra, because the original worker may already be running and could
produce overlapping writes.

A worker that returns a nonce or business result is `worker_completed`, whether or not effective-model metadata can be inspected. Record `metadata_unverified` separately; never turn this case into `start_unknown`.

Luna availability failure inserts exactly one bounded fallback:

```text
route_decided = Luna
-> Luna dispatch requested
-> Luna runtime unavailable
-> reuse same task packet
-> Terra Medium dispatch requested
-> worker_started
-> effective_model_verified (when accessible)
-> worker_completed
```

## Parent-thread permissions after route_decided

When parent != selected model/effort, the parent may only:

- construct/refine the bounded task packet;
- invoke the selected custom agent or explicit subagent;
- inspect delegation/runtime metadata;
- integrate the returned result;
- run final verification when appropriate.

It must not perform the selected worker's repository exploration, implementation, debugging, or tests before dispatch.

## Dispatch precedence

1. Registered custom agent for the selected route.
2. Explicit native subagent with exact `model` and `model_reasoning_effort` if the profile is missing/unregistered.
3. If and only if Luna itself cannot be invoked, `terra_resolver` / `gpt-5.6-terra` / `medium` with the same task packet. A transport/TLS failure stops for inspection; it does not fall back.
4. Stop if Terra fallback is also unavailable.

A missing custom-agent TOML registration alone is **not** proof that Luna is unavailable; explicit Luna spawning must be attempted first when the runtime supports it.

## What counts as Luna unavailable

Acceptable evidence includes a Luna invocation returning an error equivalent to:

- model unavailable / unsupported / not allowed;
- model-specific quota/capacity prevents starting the Luna worker;
- Luna worker cannot be created after both registered-agent and explicit-Luna invocation paths are exhausted.

Not Luna availability failures:

- sandbox setup/refresh failure;
- filesystem ACL/permission/locked file;
- missing compiler/interpreter/dependency;
- unit/integration test failure;
- repository or external service network failure;
- malformed command/task input;
- business-logic failure after Luna successfully started.

These remain environment/task failures and do not justify changing models.

## Availability fallback mapping

| Original route | Availability fallback |
|---|---|
| Luna Low | Terra Medium (`terra_resolver`) |
| Luna Medium | Terra Medium (`terra_resolver`) |
| Luna High | Terra Medium (`terra_resolver`) |

Why Terra Medium for all three: availability fallback is not evidence that the task became riskier or more ambiguous. Terra High remains reserved for its existing risk hard gates.

Use `scripts/model_availability.py` before dispatch and record every lifecycle event with `task_packet_id`, `route_decision_id`, and `dispatch_attempt_id`. Its dispatch actions are exact: `use_luna`, `probe_luna`, `use_fallback`, and `inspect_existing_probe`. The last action preserves the Luna request and prevents overlapping work; it must not request Terra.

A normal bounded business task is preferred as the half-open probe. If its worker already ran the exact parent validation command, record `verification_reused=true` instead of running it twice.

## Truthful user-visible status

Use wording that matches the strongest evidence available:

- Decision only: `[路由建议] Luna High`
- Dispatch requested: `[执行请求] Luna High｜worker=luna_deep｜实际模型待核验`
- Runtime verified: `[实际执行] Luna High｜effective_model=gpt-5.6-luna｜effort=high`
- Fallback requested/verified: `[回退执行] Terra Medium｜原因：Luna runtime unavailable`

Do not infer `effective_model` from the selected route, agent name, or TOML configuration. Prefer runtime/session `turn_context`, child-thread metadata, or equivalent execution evidence.

## Failure handling examples

### Registered agent missing

```text
luna_deep not registered
-> try explicit subagent model=gpt-5.6-luna effort=high
-> if Luna starts: continue Luna
-> if Luna invocation says unavailable: Terra Medium fallback
```

### Windows sandbox error before/around edit

```text
windows sandbox failed: helper_unknown_error
```

This is an environment failure, not Luna unavailability. Keep the selected route and report/block according to normal retry policy.

### Luna capacity/quota rejects worker start

```text
Luna dispatch -> model/capacity rejection
-> same task packet -> terra_resolver
```

Do not rescan or rewrite the packet just because the model changed.
