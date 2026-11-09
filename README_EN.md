# Codex Quota Router 1.4.2-local

Delegated workers cannot dispatch descendants by default; deeper delegation returns a blocked/escalation result to the parent without creating another worker.

[中文](README.md) | **English**

<p align="center"><img src="assets/codex-quota-router-hero.png" alt="Codex Quota Router model routing overview"></p>

Quota-aware model routing recommendations for OpenAI Codex workflows: GPT-6 Luna by default, GPT-6.1 Sol for risk and coupling gates, and GPT-6 Astra only for rare architecture planning. A route recommendation does not switch the running thread's model and is not proof that the recommended model executed.

| Model | Responsibility |
| --- | --- |
| Luna | Default, cost-efficient execution |
| Sol | Risk gates, hidden coupling, and reasoning escalation |
| Astra | Rare architecture planning and root-cause diagnosis |

```text
task → quota-first decision → Luna
                             │ risk / complexity gate
                             ▼
                           Sol → (rare) Astra
```

## Why use it

- Separates routing recommendations, execution, and effective-model evidence.
- Selects Sol only for risk/complexity gates or explicit user preference, never because Luna failed to start.
- Separates route recommendation, requested route, and runtime evidence; Luna execution failures are blockers.

## Key behavior

- Opt-in lightweight parent reuse only for adequate-effort parents and explicitly bounded tasks; hard risks and explicit model/effort choices are excluded.
- Worker counts follow independent workload, usually 0 for Low, 0-1 for Mid, and 0-2 for High, rather than fixed quotas.
- Verification reuse to avoid duplicate validation work.
- Truthful effective-model audit fields; route labels are not execution proof.
- Luna start or execution failure is reported as a blocker, with no automatic Sol reassignment.
- `disable_luna` is an explicit user preference for Sol on ordinary work; Sol High and Astra gates remain intact.

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

The deterministic helper prints the selected route:

```bash
python scripts/route_score.py --clarity 1 --scope 2 --coupling 2 --risk 2 --novelty 1
```

For delegated work, inspect worker and runtime/session evidence before claiming an effective model. If the selected route cannot execute, report the blocker; do not reassign based on model availability.

## Common overrides

- `Do not optimize quota` permits quality-first escalation.
- `Use Luna only` preserves Luna preference; if a risk gate requires another model, report the conflict.
- `disable_luna` / `这次禁用 Luna` / `$codex-quota-router 禁用 Luna：...` explicitly prefers Sol for ordinary tasks while preserving Sol High/Astra gates.
- `Route only` prints a recommendation without execution.
- `Do not use subagents` keeps work in the current thread and labels the result as a recommendation.

## Uninstallation

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
```

Linux/macOS: remove the installed skill and agent files, then restore the backed-up global `AGENTS.md` if the installer changed it.

## Design files

- `SKILL.md` — routing and execution contract.
- `references/execution-contract.md` — execution states and blocker handling.
- `references/routing-policy.md` — scoring and hard gates.
- `scripts/route_score.py` — deterministic route scoring and direct-reuse decisions.
- `agents/*.toml` — fixed model and effort profiles.
