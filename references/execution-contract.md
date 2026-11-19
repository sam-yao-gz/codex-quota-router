# Execution contract

## Honor explicit choices

Honor explicit effort and workflow constraints and reject models outside the GPT-6.2 Sol/Astra allowlist. A route recommendation is not execution evidence. If an exact model/effort conflicts with a Sol High hard-risk gate, return a clear conflict instead of lowering the gate.

## Direct execution and dispatch

The current parent should execute when its model matches and its effort meets the selected route, unless the user's workflow requires delegation. An explicitly requested effort must match exactly. No cross-model reuse or risk exception is available. Delegated workers cannot dispatch descendants.

Select the chosen route and follow the user's workflow. There is no availability preflight or automatic model fallback. If the selected model cannot start or execution fails, report a blocker; do not imply another model ran or reassign solely because of that failure. Sol is the default executor; Astra's default role is rare, read-only planning.

`route_only` means no worker dispatch. `subagents=deny` permits direct parent execution only when the parent satisfies the selected model/effort; otherwise report the selected route without dispatching.

## Execution evidence

Keep recommendation, dispatch, runtime verification, and completion distinct. When the scorer allows the parent to run, it returns `dispatch_action=direct_parent_execution_allowed`, `dispatch_allowed=false`, and the parent in `requested_*`, with the recommendation unchanged in `route_*`. The scorer leaves `parent_reused=false`, `worker_count=0`, and `effective_*` unset because it has not executed anything. Report parent reuse only after it happens, and the effective model/effort only with runtime evidence. For a worker, report the requested route and actual outcome separately.

Use worker counts based on useful independent work, not targets. Keep one writer per file, reuse concrete validation, and avoid duplicate reviewers. Join required workers before integration. Archive children through official APIs; wrapper archival is optional maintenance requiring exact official pairing and all safety checks. Missing wrapper metadata is nonblocking. Never emulate archival through database, edge, or rollout changes.
