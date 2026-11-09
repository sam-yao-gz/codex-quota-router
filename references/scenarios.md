# Routing scenarios

| Task | Recommendation | Execution note |
|---|---|---|
| Rename fields, adjust text, localized style fix | Luna Low | Parent may execute directly when workflow permits. |
| Small endpoint using an established pattern | Luna Medium | Focused tests. |
| Documented feature across 6-10 related files | Luna High | Bounded size alone is not a Sol gate. |
| Frontend/backend integration on known contracts | Luna High | Stop/escalate if ownership becomes unclear. |
| Analyze a large log and summarize | Luna Medium | Read-only; no worker needed absent a concrete benefit. |
| Same ordinary work with `quality_first` | One tier above its balanced route | Stops at Sol High; does not turn Astra planning into implementation. |
| Combined architecture marker and migration/security/production risk | Sol High | Risk gate takes priority over Astra planning. |
| Cache invalidation/idempotency or intermittent state bug | Sol Medium | Hidden state/cross-request semantics. |
| Migration, authentication, payment, race/locking, production write | Sol High | Risk hard gate; lightweight reuse denied. |
| Multi-service architecture choice | Astra Medium plan | Rare/read-only; implementation is separately routed. |
| Dependency, permission, test, network, or user-input failure | Preserve score route | Record the failure; do not escalate as reasoning failure. |

## Lightweight examples

- With explicit opt-in, an adequate supported Sol parent can handle a known two-file Luna recommendation directly. `route_model` remains Luna; `requested_model` is Sol; effective model remains unverified unless runtime evidence exists.
- A one-file task without opt-in follows ordinary routing. Exact model/effort requests are not bypassed.
- An authorized established cache-cleanup command may use the narrow validated exception only with a prevalidated whitelist, no reparse-point traversal, and locked files skipped. Unknown recursive deletion is never eligible.
- A delegated worker cannot make a child or invoke lightweight reuse as a descendant-dispatch shortcut.
- A selected model fails to start or execute: report a blocker; do not automatically assign another model.

## Common project examples

- Fund-analysis UI using documented behavior: Luna High; data mapping or cross-round idempotency: Sol Medium, Sol High if corruption is plausible.
- Workflow YAML field/type repair: Luna Medium or High.
- Cross-system call retry/idempotency: Sol Medium; production write safety: Sol High.
- Docker command/path correction: Luna Medium.
- Database architecture or major migration plan: Astra Medium for planning, Sol High for data-changing work.
