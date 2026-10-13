# Routing policy

Choose the least expensive route that can safely complete the task. Honor an explicit user model, effort, or workflow. The six existing profiles remain fixed: Luna Low/Medium/High, Sol Medium/High, and Astra Medium.

## Score

Score clarity (0-2), scope (0-3), coupling (0-3), risk (0-4), novelty (0-2), and reasoning-related failed attempts (0-2). Do not count dependency, permission, environment, or unrelated test failures.

- 0-2: Luna Low
- 3-6: Luna Medium
- 7-10: Luna High
- 11-13: Sol Medium
- 14+: Sol High

File count is weak evidence; repetitive edits may stay on Luna. Use the score helper for borderline/auditable cases, not obvious routes.

## Hard gates

- Sol Medium: hidden cross-module ownership/state, cache invalidation or idempotency semantics, intermittent behavior, or evidence-backed reasoning escalation.
- Sol High: migration/schema/data integrity, authentication/authorization, payments, concurrency, destructive or production changes, credentials/secrets, unknown deletion, plausible data loss/security exposure.
- Astra Medium: rare, read-only planning/diagnosis for a multi-system architecture choice or unresolved high-impact root cause. Return a bounded plan; route isolated implementation back to Luna when suitable.

Do not infer hidden ownership from file count. When evidence exposes cross-system ownership, data integrity, security, concurrency, or architecture decisions beyond the task boundary, stop and return the evidence for escalation.

## Lightweight parent reuse

This is opt-in and avoids dispatch overhead for a genuinely small task. It changes execution, not the recommendation: keep `route_*` as selected and report the current parent in `requested_*`; do not claim the recommended model executed.

Ordinary eligibility is limited to a Luna recommendation and a GPT-6 Luna or GPT-6.1 Sol parent with adequate effort, plus either a known maximum of 0-2 changed files or one established read-only/reversible command. This cannot bypass score-based Sol escalation. It is denied by exact model/effort requests, Luna-only policy, delegated-worker context, unsupported parent models, or risk flags/gates. Without the opt-in and boundedness evidence, legacy routing is unchanged.

One narrow deletion exception is permitted: user-authorized cache cleanup recommended as Sol High, using an established command and prevalidated whitelist, with reparse-point traversal disabled and locked files skipped. Supply the `cache`, `cache_cleanup`, and `destructive` flags plus `--validated-cache-cleanup`; the flag asserts those safeguards and does not waive them. Unknown recursive deletion, migrations, credentials, auth, production changes, or other high-risk work never qualifies.

## Coordination budget

Worker counts are workload guidance, not targets: Low usually 0, Mid usually 0-1, High usually 0-2. Use more only for independent work that saves time/context and fits client limits. Avoid overlapping writers and routine duplicate reviewers. Reuse concrete validation results.

Archive children through official APIs only. Wrapper archival is optional maintenance requiring exact official pairing and all safety gates. Missing wrapper metadata is a note, not a task blocker.

## Execution failure

There is no availability preflight or automatic model fallback. If the selected Luna route cannot start or execute, report a blocker. Sol selection must come from its risk/complexity gate or an explicit user `disable_luna` preference, never solely from Luna being unavailable.
