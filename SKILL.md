---
name: codex-quota-router
description: Route substantive Codex development and maintenance to GPT-6.2 Sol or GPT-6.2 Astra, choosing effort by task risk and reporting actual execution separately.
---

# Codex Quota Router 1.7.0

Optimize for correct completion per unit of time and quota. Honor explicit model, effort, and workflow choices; never silently downgrade the requested workflow. Recommended routes are not proof of execution.

## Route

- Default to GPT-6.2 Sol: Low for mechanical edits, Medium for ordinary work and bounded integration, High for high complexity or hard risk (data, auth/security, concurrency, destructive, or production work).
- Use GPT-6.2 Astra Medium rarely, for bounded read-only architecture/root-cause planning; route implementation to Sol. Only these two models are allowed.
- File count alone does not justify an upgrade. Use `references/routing-policy.md` for scoring and gates.
- Default to the `balanced` policy. `quality_first` promotes ordinary routes by one tier; explicit high-risk and read-only architecture routes remain governed by their hard gates. `route_only` returns a recommendation without dispatch.

## Execute

- A parent with the selected model and adequate effort should execute directly unless the user requires delegation. An explicit effort must match exactly. Do not substitute a different model. Delegated workers never dispatch descendants.
- Explicit choices outside the two-model allowlist, unsupported effort combinations, and exact choices that conflict with a Sol High hard-risk gate fail clearly. A valid choice still requires host support. A route is not permission to perform risky or destructive operations.
- Only reasoning- and logic-related failures affect the route score. Dependency, permission, test, network, and user-input failures are recorded but do not trigger reasoning escalation.
- Execution failure is a blocker; do not run availability preflights or fall back to another model.
- Report route, dispatch, runtime verification, and completion as separate facts. Set effective model/effort only with runtime evidence. Reuse exact validation already performed and returned by a worker.
- Record a unique `decision_id`, route version, policy mode, attempt index, typed failure kinds, worker count, reasoning escalation count, verification reuse, and blocker kind for each route decision.
- Honor `subagents=deny` by executing in the current parent only when its model/effort can satisfy the route; otherwise return the recommendation as blocked/route-only without claiming dispatch.

## Coordination

Worker counts are demand-based, not quotas: Low usually 0, Mid usually 0-1, High usually 0-2. Add workers only for independent work that materially saves time/context and fits the client cap. Do not add routine duplicate reviewers. Keep one writer per file; give workers bounded scope and join required workers before integration.

Archive completed children only through official APIs. Wrapper archival is optional maintenance and requires exact official pairing plus all safety checks; missing wrapper metadata is a nonblocking maintenance note. Never use direct database or rollout edits to archive.

## References

- `references/routing-policy.md`: scoring, risk gates, and allowed models.
- `references/execution-contract.md`: overrides, parent reuse, dispatch, and truthful status.
- `references/scenarios.md`: representative routes and exceptions.
- `references/task-packet.md`: concise packet template when delegation is warranted.
