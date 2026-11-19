# Routing scenarios

| Task | Recommendation | Execution note |
|---|---|---|
| Rename fields, adjust text, localized style fix | Sol Low | Parent may execute directly when workflow permits. |
| Small endpoint using an established pattern | Sol Medium | Focused tests. |
| Documented feature across 6-10 related files | Sol Medium | File count alone does not increase effort. |
| Frontend/backend integration on known contracts | Sol Medium | Stop/escalate if ownership becomes unclear. |
| Analyze a large log and summarize | Sol Medium | Read-only; no worker needed absent a concrete benefit. |
| Same ordinary work with `quality_first` | One tier above its balanced route | Stops at Sol High; does not turn Astra planning into implementation. |
| Combined architecture marker and migration/security/production risk | Sol High | Risk gate takes priority over Astra planning. |
| Cache invalidation/idempotency or intermittent state bug | Sol Medium | Hidden state/cross-request semantics. |
| Migration, authentication, payment, race/locking, production write | Sol High | Risk hard gate; routing is not action authorization. |
| Multi-service architecture choice | Astra Medium plan | Rare/read-only; implementation is separately routed. |
| Dependency, permission, test, network, or user-input failure | Preserve score route | Record the failure; do not escalate as reasoning failure. |

## Execution examples

- An adequate parent on the same model can handle a route without a worker; an explicit effort must match exactly. A parent on another model cannot substitute.
- Cache cleanup routes to Sol High and requires separate authorization and a validated scope.
- A delegated worker cannot make a child or reuse a different model as a shortcut.
- A selected model fails to start or execute: report a blocker; do not automatically assign another model.

## Common project examples

- Fund-analysis UI using documented behavior: Sol Medium; data mapping or cross-round idempotency: Sol Medium, Sol High if corruption is plausible.
- Workflow YAML field/type repair: Sol Low or Medium, depending on coupling.
- Cross-system call retry/idempotency: Sol Medium; production write safety: Sol High.
- Docker command/path correction: Sol Low or Medium.
- Database architecture or major migration plan: Astra Medium for planning, Sol High for data-changing work.
