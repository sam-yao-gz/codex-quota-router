# Changelog

All notable changes to this project are documented here.

## [1.3.1] - 2026-08-09

### Added

- Explicit `disable_luna` user policy with natural-language and CLI inputs.
- Availability-state-preserving Terra/Sol routing and auditable zero probe/fallback counts.
- Risk/architecture hard gates remain Terra High/Sol Medium when Luna is disabled.

### Changed

- README and execution contract now distinguish user-directed Luna bypass from model unavailability fallback.

## [1.3.0] - 2026-08-09

### Added

- Quota-first Luna default with Terra escalation and rare Sol planning.
- 300-second half-open lease and stale recovery for availability probes.
- Business-task recovery probes, parent reuse, single-worker default, and verification reuse.
- Explicit separation of transport/TLS failures from model unavailability.
- Truthful effective-model audit states and execution evidence.

### Changed

- Release documentation now reflects the v1.3.0 execution and availability contracts.
