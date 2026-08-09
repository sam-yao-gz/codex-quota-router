<!-- BEGIN CODEX_LUNA_FIRST_ROUTER -->
## Luna-first automatic model routing

- For every substantive implementation, debugging, refactor, code review, testing, workflow, infrastructure, or codebase-analysis task, invoke `$codex-quota-router` before broad repository reads or edits.
- A routing label is not execution. If the selected model/effort differs from the current parent, **delegate before substantive work** and do not let the parent continue the selected worker's task.
- Default strongly to Luna. Prefer the registered Luna agent; if the profile is unavailable, explicitly request a Luna subagent with the exact model/effort.
- If Luna itself cannot be invoked because the Luna model/runtime is unavailable, reuse the same bounded packet and fall back to Terra Medium. Do not classify sandbox, ACL, dependency, test, or project-service failures as Luna unavailability.
- Before Luna dispatch, use `scripts/model_availability.py` to read/decide the persistent circuit. Open circuits dispatch Terra Medium; cooldown expiry permits exactly one half-open probe. Record `start_rejected` separately from `start_unknown`: only explicit availability rejection may fall back, while unknown starts require child/session inspection before any Terra dispatch.
- Never claim “Luna executed” without runtime/session evidence; when effective model cannot be inspected, say it is unverified.
- Keep Sol rare and primarily for bounded architecture/root-cause planning.
- Do not bypass an explicit model or reasoning choice from the user.
<!-- END CODEX_LUNA_FIRST_ROUTER -->
