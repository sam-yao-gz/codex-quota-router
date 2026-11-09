# Codex Quota Router 1.5.0

[中文](README.md) | **English**

<p align="center"><img src="assets/codex-quota-router-hero.png" alt="Codex Quota Router model routing overview"></p>

Auditable model-routing recommendations for OpenAI Codex workflows: GPT-6 Luna by task, GPT-6.1 Sol for risk gates and hidden coupling, and GPT-6 Astra for rare read-only architecture planning. A recommendation does not switch the running thread's model or prove that the target model executed.

| Model | Responsibility |
| --- | --- |
| Luna | Default execution at Low, Medium, or High effort as the task requires |
| Sol | High-risk gates, hidden coupling, and reasoning escalation |
| Astra | Rare read-only architecture planning and root-cause diagnosis |

## Policies

- `balanced` (default): use score bands and hard risk gates to select the least expensive adequate route.
- `quality_first`: promote ordinary routes by one tier; preserve Sol High risk gates and the read-only Astra architecture role.
- `route_only`: return a recommendation and audit record without dispatching a worker.
- `subagents=auto|allow|deny`: control delegation separately; with `deny`, execute directly only if the current parent satisfies the selected route.
- Honor explicit model and effort choices. Validate effort against each model's capabilities; reject unknown models, combinations, and flags rather than silently downgrading. If an exact choice conflicts with a Sol High hard-risk gate, return a conflict instead of weakening the gate.

Explicit effort levels exposed by the current Codex host:

| Model | Supported effort |
| --- | --- |
| `gpt-6-luna` | `none`, `low`, `medium`, `high`, `xhigh`, `max` |
| `gpt-6.1-sol` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| `gpt-6-astra` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |

Default routing continues to use the six installed agent profiles. Higher explicit effort applies only when the execution mechanism supports and actually passes it through.

## Installation

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Use `-SkipGlobalAutoRouting` to avoid changing the global routing file.

### Linux/macOS

```bash
chmod +x install.sh
./install.sh
```

Use `SKIP_GLOBAL_AUTO_ROUTING=1 ./install.sh` to skip the global file. Restart Codex after installation.

## Validation

```bash
python scripts/validate_skill.py
python scripts/run_tests.py
```

The score helper returns route and audit data; it does not dispatch a worker or prove model execution. Set effective model/effort only with runtime evidence. Only reasoning and logic failures increase the route score. Dependency, permission, test, network, and user-input blockers are recorded by kind and do not trigger model escalation.

## Uninstallation

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
```

Linux/macOS: remove the installed skill and agent files, then restore the backed-up global `AGENTS.md` if the installer changed it.

## Design files

- `SKILL.md` — routing and execution contract.
- `references/execution-contract.md` — execution states and blocker handling.
- `references/routing-policy.md` — policies, score bands, effort levels, and risk gates.
- `scripts/route_score.py` — deterministic route scoring and policy validation.
- `agents/*.toml` — the six default model/effort profiles.
