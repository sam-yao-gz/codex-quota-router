# Routing policy

Choose the least expensive route that can safely complete the task. Honor explicit model, effort, and workflow choices when compatible with hard-risk gates; reject an incompatible exact choice instead of silently lowering a gate. The six installed profiles remain fixed: Luna Low/Medium/High, Sol Medium/High, and Astra Medium. Explicit user efforts may use additional levels supported by the selected model.

## Policy modes

- `balanced` (default): use the score bands and risk gates below.
- `quality_first`: promote ordinary Luna Low to Luna Medium, Luna Medium to Luna High, Luna High to Sol Medium, and Sol Medium to Sol High. Do not weaken Sol High risk gates or change the read-only Astra architecture route.
- `route_only`: return the recommendation and audit record without dispatching work.
- `subagents=auto|allow|deny` records delegation preference separately from the route. With `deny`, execute directly only when the current parent satisfies the selected model and effort; otherwise stop at a route-only recommendation.

## Score

Score clarity (0-2), scope (0-3), coupling (0-3), risk (0-4), novelty (0-2), and up to two reasoning- or logic-related failures (0-2). Record dependency, permission, test, network, and user-input failures as typed failures; never count them as reasoning escalation.

- 0-2: Luna Low
- 3-6: Luna Medium
- 7-10: Luna High
- 11-13: Sol Medium
- 14+: Sol High

File count is weak evidence; repetitive edits may stay on Luna. Use the score helper for borderline/auditable cases, not obvious routes.

## Hard gates

Apply hard gates in this order. Risk dominates planning: when a request combines an architecture/planning marker with a Sol High risk marker, select Sol High.

- Sol High: migration/schema/data integrity, authentication/authorization, payments, concurrency, destructive or production changes, credentials/secrets, unknown deletion, plausible data loss/security exposure.
- Sol Medium: hidden cross-module ownership/state, cache invalidation or idempotency semantics, intermittent behavior, or evidence-backed reasoning escalation.
- Astra Medium: rare, read-only planning/diagnosis for a multi-system architecture choice or unresolved high-impact root cause. Return a bounded plan; route isolated implementation back to Luna when suitable.

Do not infer hidden ownership from file count. When evidence exposes cross-system ownership, data integrity, security, concurrency, or architecture decisions beyond the task boundary, stop and return the evidence for escalation.

## Lightweight parent reuse

This is opt-in and avoids dispatch overhead for a genuinely small task. It changes execution, not the recommendation: keep `route_*` as selected and report the current parent in `requested_*`; do not claim the recommended model executed.

Ordinary eligibility is limited to a Luna recommendation and a GPT-6 Luna or GPT-6.1 Sol parent with adequate effort, plus either a known maximum of 0-2 changed files or one established read-only/reversible command. This cannot bypass score-based Sol escalation. It is denied by exact model/effort requests, delegated-worker context, unsupported parent models, or risk flags/gates. Without the opt-in and boundedness evidence, ordinary routing is unchanged.

One narrow deletion exception is permitted: user-authorized cache cleanup recommended as Sol High, using an established command and prevalidated whitelist, with reparse-point traversal disabled and locked files skipped. Supply the `cache`, `cache_cleanup`, and `destructive` flags plus `--validated-cache-cleanup`; the flag asserts those safeguards and does not waive them. Unknown recursive deletion, migrations, credentials, auth, production changes, or other high-risk work never qualifies.

## Coordination budget

Worker counts are workload guidance, not targets: Low usually 0, Mid usually 0-1, High usually 0-2. Use more only for independent work that saves time/context and fits client limits. Avoid overlapping writers and routine duplicate reviewers. Reuse concrete validation results.

Archive children through official APIs only. Wrapper archival is optional maintenance requiring exact official pairing and all safety gates. Missing wrapper metadata is a note, not a task blocker.

## Execution failure

There is no availability preflight or automatic model fallback. If the selected route cannot start or execute, report a blocker. Never re-route solely because the selected model is unavailable.

## Effort and model validation

Accept explicit model/effort only when the model is in the registry and the effort is supported for it. The current registry is:

| Model | Supported explicit efforts |
|---|---|
| `gpt-6-luna` | `none`, `low`, `medium`, `high`, `xhigh`, `max` |
| `gpt-6.1-sol` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| `gpt-6-astra` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |

Default agent routing continues to use only the six installed profiles. Explicit higher effort is an override and must be passed through to an execution mechanism that supports that exact model/effort; a profile name alone is not proof that the override ran.

## Typed failures and audit

Accept `reasoning`, `logic`, `dependency`, `permission`, `test`, `network`, and `user_input` failure kinds. Only the first two can increase the score. Each decision records a unique `decision_id`, `route_version`, `policy_mode`, `attempt_index`, failure kinds, `worker_count`, `reasoning_escalation_count`, `verification_reused`, and `blocker_kind`. These are decision audit fields, not proof of execution.

Flags must belong to the helper's known-flag registry. Unknown flags and unknown explicit model names fail instead of silently routing as ordinary work.
