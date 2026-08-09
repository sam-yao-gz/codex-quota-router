# Codex Quota Router v1.3.0

[中文](README.md) | **English**

Quota-first routing for OpenAI Codex workflows. Luna is the default; Terra is an evidence-based escalation, and Sol is reserved for rare architecture-level planning. The default concurrency is one task to one worker.

```text
task → quota-first decision → Luna
                             │ unavailable / hard gate
                             ▼
                           Terra → (rare) Sol
```

## Why use it

- Separates routing recommendations, execution, and effective-model evidence.
- Avoids duplicate workers while preserving a bounded Luna-to-Terra availability fallback.
- Keeps unavailable, transport/TLS, and metadata-unknown outcomes explicit instead of guessing.

## v1.3.0 highlights

- 300-second half-open lease with stale-probe recovery.
- Business-task recovery probes instead of health-only workers.
- Parent reuse when the current model and effort already satisfy the route.
- Default concurrency of one task and one worker.
- Verification reuse to avoid duplicate validation work.
- Transport/TLS failures remain distinct from model unavailability.
- Truthful effective-model audit fields; route labels are not execution proof.

## Installation

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

To avoid changing the global routing file:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -SkipGlobalAutoRouting
```

### Linux/macOS

```bash
chmod +x install.sh
./install.sh
```

Use `SKIP_GLOBAL_AUTO_ROUTING=1 ./install.sh` to skip the global file. Restart Codex after installation.

## Validation

Run the structural check:

```bash
python scripts/validate_skill.py
```

The deterministic scoring helper can simulate fallback:

```bash
python scripts/route_score.py --clarity 1 --scope 2 --coupling 2 --risk 2 --novelty 1 --luna-unavailable
```

For delegated work, inspect independent worker and runtime/session evidence before claiming an effective model. A clear Luna runtime rejection may create a Terra worker; sandbox, ACL, dependency, test, and transport failures are not model-unavailable signals.

## Common overrides

- `Do not optimize quota` permits quality-first escalation.
- `Use Luna only` disables availability fallback and reports a blocker if Luna cannot start.
- `Route only` prints a recommendation without execution.
- `Do not use subagents` keeps work in the current thread and labels the result as a recommendation.

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
