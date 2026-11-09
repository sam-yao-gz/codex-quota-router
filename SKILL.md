---
name: codex-quota-router
description: Route substantive Codex work to an appropriate GPT-6 profile while preserving explicit choices, truthful execution evidence, and quota-aware direct reuse.
---

# Codex Quota Router 1.4.2-local

Optimize for correct completion per unit of time and quota. Honor explicit model, effort, and workflow choices; never silently downgrade the requested workflow. Recommended routes are not proof of execution.

## Route

- Default to GPT-6 Luna: Low for mechanical edits, Medium for ordinary bounded work, High for nontrivial bounded integration.
- Use GPT-6.1 Sol Medium for hidden coupling, unclear ownership, or reasoning escalation; Sol High for data integrity, auth/security, concurrency, and destructive or production risk.
- Use GPT-6 Astra Medium rarely, for bounded read-only architecture/root-cause planning. Keep the six installed agent profiles unchanged.
- File count alone does not justify an upgrade. Use `references/routing-policy.md` for scoring and gates.

## Execute

- A parent with the selected model and adequate effort may execute directly. Otherwise delegate unless the opt-in lightweight rule below applies. Do not claim the recommended model executed when the current parent performed the work.
- Lightweight reuse is opt-in and ordinarily limited to Luna recommendations with a GPT-6 Luna/Sol parent, adequate effort, and either at most two known changed files or one established read-only/reversible command. It cannot bypass score-based Sol routes. Exact model/effort, Luna-only, migrations, auth, payments, concurrency, unclear/destructive operations, production changes, and other hard risk gates are excluded. The sole destructive exception is a user-authorized, established cache cleanup with a prevalidated whitelist, no reparse-point traversal, and locked files skipped; this does not relax those safeguards. Delegated workers never dispatch descendants.
- The route helper preserves ordinary routing unless `--allow-lightweight-reuse` and boundedness evidence are supplied. Read `references/execution-contract.md` for result fields.
- Execution failure is a blocker; no availability preflight or automatic Sol fallback is performed. Choose Sol only for its risk/complexity gates or an explicit user `disable_luna` preference; Astra remains rare planning.
- Report route, dispatch, runtime verification, and completion as separate facts. Set effective model/effort only with runtime evidence. Reuse exact validation already performed and returned by a worker.

## Coordination

Worker counts are demand-based, not quotas: Low usually 0, Mid usually 0-1, High usually 0-2. Add workers only for independent work that materially saves time/context and fits the client cap. Do not add routine duplicate reviewers. Keep one writer per file; give workers bounded scope and join required workers before integration.

Archive completed children only through official APIs. Wrapper archival is optional maintenance and requires exact official pairing plus all safety checks; missing wrapper metadata is a nonblocking maintenance note. Never use direct database or rollout edits to archive.

## References

- `references/routing-policy.md`: scoring, risk gates, and lightweight eligibility.
- `references/execution-contract.md`: overrides, parent reuse, dispatch, and truthful status.
- `references/scenarios.md`: representative routes and exceptions.
- `references/task-packet.md`: concise packet template when delegation is warranted.
