# Changelog

All notable changes to this project are documented here.

## [1.4.0] - 2026-10-08

### Changed

- Route Luna work to GPT-6 Luna, Sol fallback/risk work to GPT-6.1 Sol, and architecture planning to GPT-6 Astra.
- Scope availability state to GPT-6 Luna, migrate managed agent profiles and global marker handling, and preserve an in-place skill checkout during installation.

## [1.3.2] - 2026-08-25

### Added

- Delegated-worker recursion guard: descendants are denied by default and deeper delegation is reported to the parent as blocked/escalation.

## [1.3.1] - 2026-08-09

### Added

- Explicit `disable_luna` user policy with natural-language and CLI inputs.
- Availability-state-preserving Sol/Astra routing and auditable zero probe/fallback counts.
- Risk/architecture hard gates remain Sol High/Astra Medium when Luna is disabled.

### Changed

- README and execution contract now distinguish user-directed Luna bypass from model unavailability fallback.

## [1.3.0] - 2026-08-09

### Added

- Quota-first Luna default with Sol escalation and rare Astra planning.
- 300-second half-open lease and stale recovery for availability probes.
- Business-task recovery probes, parent reuse, single-worker default, and verification reuse.
- Explicit separation of transport/TLS failures from model unavailability.
- Truthful effective-model audit states and execution evidence.

### Changed

- Release documentation now reflects the v1.3.0 execution and availability contracts.
