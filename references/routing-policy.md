# Routing policy

Choose the least expensive eligible route that can safely complete the task. Only GPT-6.2 Sol and GPT-6.2 Astra are allowed, including for explicit requests. The four profiles are Sol Low/Medium/High and Astra Medium.

## Policy modes

- `balanced` (default): use the score bands and risk gates below.
- `quality_first`: promote ordinary Sol Low to Sol Medium and Sol Medium to Sol High. Do not weaken Sol High risk gates or change the read-only Astra architecture route.
- `route_only`: return the recommendation and audit record without dispatching work.
- `subagents=auto|allow|deny` records delegation preference separately from the route. With `deny`, execute directly only when the current parent satisfies the selected model and effort; otherwise stop at a route-only recommendation.

## Score

Score clarity (0-2), scope (0-3), coupling (0-3), risk (0-4), novelty (0-2), and up to two reasoning- or logic-related failures (0-2). Record dependency, permission, test, network, and user-input failures as typed failures; never count them as reasoning escalation.

- 0-2: Sol Low
- 3-10: Sol Medium
- 11+: Sol High

File count is weak evidence; repetitive edits may stay at Low effort. Use the score helper for borderline/auditable cases, not obvious routes.

## Hard gates

Apply hard gates in this order. Risk dominates planning: when a request combines an architecture/planning marker with a Sol High risk marker, select Sol High.

- Sol High: migration/schema/data integrity, authentication/authorization, payments, concurrency, destructive or production changes, credentials/secrets, cleanup/deletion, plausible data loss/security exposure.
- Astra Medium: rare, read-only planning/diagnosis for a multi-system architecture choice or unresolved high-impact root cause. Return a bounded plan; route implementation to Sol.
- Sol Medium minimum: hidden cross-module ownership/state, cache invalidation or idempotency semantics, intermittent behavior, or evidence-backed reasoning escalation. This does not lower a High score.

Do not infer hidden ownership from file count. When evidence exposes cross-system ownership, data integrity, security, concurrency, or architecture decisions beyond the task boundary, stop and return the evidence for escalation.

## Parent execution

Reuse the current parent only when it matches the selected model and has adequate effort. An explicit effort must match exactly. Routing does not authorize actions. Where cache cleanup is separately authorized, use a validated whitelist, avoid reparse-point traversal, and skip locked files.

## Coordination budget

Worker counts are workload guidance, not targets: Low usually 0, Mid usually 0-1, High usually 0-2. Use more only for independent work that saves time/context and fits client limits. Avoid overlapping writers and routine duplicate reviewers. Reuse concrete validation results.

Archive children through official APIs only. Wrapper archival is optional maintenance requiring exact official pairing and all safety gates. Missing wrapper metadata is a note, not a task blocker.

## Execution failure

There is no availability preflight or automatic model fallback. If the selected route cannot start or execute, report a blocker. Never re-route solely because the selected model is unavailable.

## Effort and model validation

Accept explicit model/effort only when the model is in the registry and the effort is supported for it. This is the router's offline allowlist, not a runtime entitlement check:

| Model | Supported explicit efforts | Routing |
|---|---|---|
| `gpt-6.2-sol`, `gpt-6.2-astra` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` | Active |

Default agent routing uses the four installed profiles. The hard-risk gate requires Sol High. An explicit override must be passed through to an execution mechanism that supports the exact model/effort and the user's delegation constraints; a role name alone is not proof that the override ran. Consult the [Codex model guide](https://developers.openai.com/codex/models) when updating the allowlist.

## Typed failures and audit

Accept `reasoning`, `logic`, `dependency`, `permission`, `test`, `network`, and `user_input` failure kinds. Only the first two can increase the score. Each decision records a unique `decision_id`, `route_version`, `policy_mode`, `attempt_index`, failure kinds, `worker_count`, `reasoning_escalation_count`, `verification_reused`, and `blocker_kind`. These are decision audit fields, not proof of execution.

Flags must belong to the helper's known-flag registry. Unknown flags and unknown explicit model names fail instead of silently routing as ordinary work.
