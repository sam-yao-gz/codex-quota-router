# Routing scenarios

| Task | Route | Why |
|---|---|---|
| Rename fields, adjust text, update CSS spacing | Luna Low | Mechanical and reversible |
| Add a small endpoint following an existing pattern | Luna Medium | Clear implementation and tests |
| Fix a YAML workflow import error | Luna Medium | Structured, bounded repair |
| Implement a documented page across 6-10 related files | Luna High | Multi-file but bounded |
| Frontend/backend integration using existing contracts | Luna High | Normal coupling, clear behavior |
| Trace a large log and summarize likely failure point | Luna Medium | Read-heavy, no risky writes |
| Add tests to an existing feature | Luna Medium | Repeatable and verifiable |
| Refactor many files with the same deterministic change | Luna High | Large scope but low novelty |
| Cache invalidation or idempotency bug | Terra Medium | Hidden state and cross-request semantics |
| Intermittent bug spanning several modules | Terra Medium | Root cause is not local |
| Database migration with rollback | Terra High | Data integrity risk |
| Authentication or permission change | Terra High | Security boundary |
| Locking/race-condition fix | Terra High | Concurrency correctness |
| Production outage repair | Terra High | Availability risk; Sol only if no coherent root cause |
| Choose architecture for a multi-service redesign | Sol Medium plan, then Luna High/Terra implementation | Expensive reasoning is confined to planning |
| Luna High failed because a dependency was missing | Stay Luna High | Not a reasoning failure |
| Luna High produced two contradictory root causes | Terra Medium | Evidence supports escalation |
| Terra cannot explain an architecture-level failure | Sol Medium diagnosis | Rare escalation |

| Luna High selected while parent is Terra Ultra | Delegate to `luna_deep` before substantive work | Route decision must become an actual worker, not a label |
| `luna_deep` profile missing but explicit Luna spawn works | Luna High via explicit subagent | Missing profile is not Luna model unavailability |
| Luna model/capacity rejects worker start | Terra Medium using same task packet | Availability fallback, not complexity escalation |
| Luna worker starts but Windows sandbox edit fails | Stay on selected route / report environment blocker | Sandbox failure is not Luna model unavailability |

## Examples aligned to common projects

- Fund-analysis platform UI interaction changes: Luna High when the design is already documented.
- Fund data mapping, snapshot availability, or cross-round idempotency: Terra Medium; Terra High if data corruption is possible.
- WeAgent workflow YAML field/type repair: Luna Medium or High.
- 400-call assistant cross-system idempotency and retry design: Terra Medium; Terra High for production write safety.
- Docker Compose command/path corrections: Luna Medium.
- Database architecture or major migration plan: Sol Medium plan, Terra/Luna execution.
