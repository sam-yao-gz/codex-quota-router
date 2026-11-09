<!-- BEGIN CODEX_QUOTA_ROUTER -->
## GPT-6 quota-aware routing

- Honor explicit model, effort, and workflow choices. A route recommendation is not execution evidence; report the model that actually ran, or mark it unverified.
- Use `balanced` by default; `quality_first` promotes ordinary routes one tier, while Sol High risk gates take precedence over Astra planning. `route_only` returns a recommendation without dispatch.
- Validate explicit effort against the selected model's capabilities; reject unknown combinations and exact choices that conflict with Sol High hard-risk gates instead of silently weakening the gate.
- Default to GPT-6 Luna for bounded work; use GPT-6.1 Sol Medium for hidden coupling/escalation and Sol High for data, auth/security, concurrency, destructive, or production risk. Keep Astra rare for bounded, read-only architecture planning.
- Treat subagent preference separately from route selection. When subagents are denied, execute in the parent only if its model and effort satisfy the selected route; otherwise return the recommendation without dispatch.
- Direct execution by the current parent is acceptable when its effort and the user's workflow permit. Opt-in lightweight reuse ordinarily applies only to Luna recommendations with a GPT-6 Luna/Sol parent, adequate effort, and tasks bounded to at most two files or one established read-only/reversible command; it cannot bypass score-based Sol escalation. Exact model/effort, delegated-worker, and hard-risk cases are excluded. The Sol High cache-cleanup exception retains authorization, whitelist, no-reparse traversal, and locked-file safeguards.
- If the selected route cannot start or execution fails, report a blocker. Do not run availability preflights/probes or automatically reassign models.
- Workers are demand-based (Low usually 0, Mid 0-1, High 0-2), not quotas. Delegate only for meaningful independent savings within client limits; keep one writer per file and reuse validation.
- Archive children only through official APIs. Wrapper archival is optional maintenance requiring exact official pairing and every safety check; missing metadata is nonblocking. Never edit databases or rollout files to emulate archival.
- In an actual project, read its root `AGENTS.md` first; use `E:\guanwang\个人工作代理\START_HERE.md` only when the project root is unconfirmed or work is cross-project.
<!-- END CODEX_QUOTA_ROUTER -->
