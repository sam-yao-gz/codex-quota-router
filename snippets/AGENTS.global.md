<!-- BEGIN CODEX_QUOTA_ROUTER -->
## GPT-6.2 quota-aware routing

- Allow only GPT-6.2 Sol and GPT-6.2 Astra, including explicit requests. Honor compatible effort and workflow choices. Report actual execution only with runtime evidence.
- Use `balanced` by default; `quality_first` promotes ordinary routes one tier, while Sol High risk gates take precedence over Astra planning. `route_only` returns a recommendation without dispatch.
- Validate explicit effort against the selected model's capabilities; reject unknown combinations and exact choices that conflict with Sol High hard-risk gates instead of silently weakening the gate.
- Default to GPT-6.2 Sol Low, Medium, or High by task complexity. Use Sol High for data, auth/security, concurrency, destructive, or production risk. Use GPT-6.2 Astra rarely for bounded, read-only architecture planning.
- Treat subagent preference separately from route selection. When subagents are denied, execute in the parent only if its model and effort satisfy the selected route; otherwise return the recommendation without dispatch.
- Prefer direct execution when the current parent matches the selected model, has adequate effort, and the user's workflow permits it. Explicit effort must match exactly. Do not use a different model or treat routing as action authorization.
- If the selected route cannot start or execution fails, report a blocker. Do not run availability preflights/probes or automatically reassign models.
- Workers are demand-based (Low usually 0, Mid 0-1, High 0-2), not quotas. Delegate only for meaningful independent savings within client limits; keep one writer per file and reuse validation.
- Archive children only through official APIs. Wrapper archival is optional maintenance requiring exact official pairing and every safety check; missing metadata is nonblocking. Never edit databases or rollout files to emulate archival.
- In an actual project, read its root `AGENTS.md` first; use `E:\guanwang\个人工作代理\START_HERE.md` only when the project root is unconfirmed or work is cross-project.
<!-- END CODEX_QUOTA_ROUTER -->
