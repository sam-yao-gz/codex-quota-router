# Luna-first routing policy

This policy intentionally accepts a small increase in retry risk to preserve quota. The default should remain Luna unless evidence justifies an upgrade.

## Score dimensions

### Clarity

- 0: Exact target and acceptance criteria are known.
- 1: One material detail must be inferred from nearby code.
- 2: Desired behavior, ownership, or success criteria are ambiguous.

### Scope

- 0: Text-only or one tiny file.
- 1: One to five related files.
- 2: Six to fifteen files or one subsystem.
- 3: More than fifteen files or repository-wide change.

File count is weak evidence. Repetitive changes can still use Luna.

### Coupling

- 0: Isolated edit.
- 1: One module or clear call path.
- 2: Multiple modules or frontend/backend interaction.
- 3: Multiple services, storage systems, queues, external platforms, or unclear ownership.

### Risk

- 0: Docs, comments, formatting, generated artifacts.
- 1: Normal reversible code change.
- 2: User-visible behavior or externally consumed API.
- 3: Data integrity, auth, deployment, production availability, concurrency, or rollback concerns.
- 4: Plausible irreversible loss, security exposure, financial impact, or outage amplification.

### Novelty

- 0: Existing local pattern can be copied.
- 1: New local pattern or unfamiliar dependency.
- 2: New architecture, undocumented behavior, or uncertain external semantics.

### Failed focused attempts

- 0: None.
- 1: One competent, bounded attempt failed for a reasoning-related cause.
- 2: Two competent attempts failed or produced contradictory diagnoses.

Do not count environment, dependency, permission, or unrelated test failures.

## Tight-profile thresholds

Total the dimensions.

- 0-2: Luna Low
- 3-6: Luna Medium
- 7-10: Luna High
- 11-13: Terra Medium
- 14+: Terra High

The thresholds already favor Luna. Do not add an additional “just in case” upgrade.

## Hard gates

### Force at least Terra Medium

- cache invalidation or idempotency across requests;
- intermittent state-dependent bug;
- cross-module behavior with unclear source of truth;
- one failed focused Luna High attempt caused by incorrect reasoning.

### Force at least Terra High

- data/schema migration;
- authentication or authorization;
- payment or billing behavior;
- race condition, locking, transaction isolation, or distributed consistency;
- destructive filesystem/database operation;
- production incident fix or rollback plan;
- plausible data loss or security exposure.

### Use Sol Medium for planning/diagnosis

Use only when at least one condition holds:

- architecture choice affects several systems and has multiple viable designs;
- Terra produced no coherent root cause after a competent attempt;
- a high-impact change cannot be safely decomposed without first resolving fundamental uncertainty.

Sol should return a bounded plan, invariants, file boundaries, and verification criteria. Implementation then routes downward.

## Budget rules

- Default concurrency: one worker.
- A second Luna read-only worker requires all of: independent scope, no overlapping writes, a documented reason it reduces parent context, and an explicit parent decision.
- Maximum reasoning by default: High.
- Sol default effort: Medium.
- No Ultra, Pro, XHigh, or Max unless the user explicitly requests a quality-first override.
- Never repeat full repository scans. Reuse summaries and target lists.
- Keep raw logs in worker threads; return distilled evidence to the parent.

## Availability fallback is not a complexity escalation

If a selected Luna worker cannot be started because the Luna model/runtime is unavailable, reuse the same bounded task packet with `terra_resolver` / Terra Medium. Do not add score or reinterpret the task as more risky merely because Luna is unavailable.

A missing registered Luna profile alone is not enough: try explicit Luna model+effort delegation first. Sandbox, permission, dependency, test, or project-service failures are environment/task failures and do not trigger this fallback.

## Quota-first dispatch and reuse

The route scorer returns exactly one action: `use_luna`, `probe_luna`, `use_fallback`, or `inspect_existing_probe`. `probe_luna` always requests Luna, so no result can combine a probe action with requested Terra. A transport/TLS result stops and is audited; it is neither a Luna availability rejection nor a fallback trigger.

Parent reuse is a pure compatibility rule: same model plus parent effort greater than or equal to target effort may reuse the parent. Cross-model paths always delegate. A high-effort same-model parent therefore may perform a medium- or low-effort target without spawning another worker.
