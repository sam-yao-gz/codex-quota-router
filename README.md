# Codex Quota Router v1.3.0

Quota-first routing for OpenAI Codex work. Luna is the default; Terra is an evidence-based escalation; Sol is rare and reserved for architecture-level planning. By default, one task is assigned to one worker.

```text
task -> quota-first decision -> Luna
                         | unavailable / hard gate
                         v
                       Terra -> (rare) Sol
```

## Why use it

- Keeps routing decisions separate from execution and effective-model evidence.
- Avoids unnecessary duplicate workers while preserving safe availability fallback.
- Makes unavailable, transport/TLS, and metadata-unknown outcomes explicit instead of guessing.

## v1.3 highlights

- 300-second half-open lease with stale-probe recovery.
- Business-task recovery probes instead of health-only workers.
- Parent reuse when the current model and effort already satisfy the route.
- Default concurrency of 1: one task, one worker.
- Verification reuse to avoid duplicate validation work.
- Transport/TLS failures remain distinct from model unavailability.
- Truthful effective-model audit fields; route labels alone are not execution proof.

## Installation

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

The installer copies the skill to `%USERPROFILE%\.agents\skills\codex-quota-router`, installs six agents under `%USERPROFILE%\.codex\agents`, and backs up before updating `%USERPROFILE%\.codex\AGENTS.md`.

To avoid changing the global routing file:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -SkipGlobalAutoRouting
```

### Linux/macOS

```bash
chmod +x install.sh
./install.sh
```

Use `SKIP_GLOBAL_AUTO_ROUTING=1 ./install.sh` to skip the global file.

## Verification

Run the structural check:

```bash
python scripts/validate_skill.py
```

Restart Codex and test with a parent model different from the selected route. Confirm an independent worker when delegation is required, and inspect runtime/session evidence before claiming an effective model. A clear Luna model/runtime rejection should create a new Terra worker; sandbox, ACL, dependency, test, and transport failures are not model-unavailable signals.

The deterministic scoring helper can simulate fallback:

```bash
python scripts/route_score.py --clarity 1 --scope 2 --coupling 2 --risk 2 --novelty 1 --luna-unavailable
```

## Common overrides

- “Do not optimize quota” permits quality-first escalation.
- “Use Luna only” disables availability fallback and reports a blocker if Luna cannot start.
- “Route only” prints a recommendation without execution.
- “Do not use subagents” keeps work in the current thread and labels the result as a recommendation.

## Uninstallation

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
```

Linux/macOS: remove the installed skill and agent files, then restore the backed-up global `AGENTS.md` if the installer changed it.

## Design files

- `SKILL.md` — routing, quota-first availability controller, and execution contract.
- `references/execution-contract.md` — execution states and fallback boundaries.
- `references/routing-policy.md` — scoring and hard gates.
- `scripts/route_score.py` — deterministic route scoring and fallback simulation.
- `agents/*.toml` — fixed model and effort profiles.
