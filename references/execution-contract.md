# Execution contract

## Honor explicit choices

Honor explicit model, effort, and workflow constraints. A route recommendation is not execution evidence. Do not turn an exact model/effort request into cross-model reuse or a different workflow. `disable_luna` is an explicit user preference: ordinary Luna routes map to Sol Medium while existing Sol High/Astra gates remain. A conflict with Luna-only is reported, not silently resolved.

## Direct execution and dispatch

The current parent may execute when its model and effort satisfy the selected route. Optional lightweight reuse is opt-in and ordinarily limited to a Luna recommendation, supported GPT-6 Luna/Sol parent, adequate effort, and known scope (at most two files or one established read-only/reversible command). It cannot bypass score-based Sol escalation. Hard risks and exact overrides fail closed. The narrow Sol High cache-cleanup exception requires user authorization, a prevalidated whitelist, no reparse-point traversal, and locked files skipped. Delegated workers cannot dispatch descendants.

Select the chosen route and follow the user's workflow. There is no availability preflight, circuit, probe, unknown-start ceremony, or automatic Sol fallback. If Luna cannot start or execution fails, report a blocker; do not imply another model ran or reassign solely because of that failure. Sol remains available for its risk/complexity gates and explicit `disable_luna`; Astra is rare bounded planning.

## Execution evidence

Keep recommendation, dispatch, runtime verification, and completion distinct. A direct parent reuse has `dispatch_action=direct_parent_reuse`, `parent_reused=true`, and the current parent in `requested_*`; keep the recommendation in `route_*`. `effective_*` stays unset without runtime evidence. For a worker, report the requested route and actual outcome separately. Missing runtime model metadata is unverified, not proof that another model executed.

Use worker counts based on useful independent work, not targets. Keep one writer per file, reuse concrete validation, and avoid duplicate reviewers. Join required workers before integration. Archive children through official APIs; wrapper archival is optional maintenance requiring exact official pairing and all safety checks. Missing wrapper metadata is nonblocking. Never emulate archival through database, edge, or rollout changes.
