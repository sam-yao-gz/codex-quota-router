# Codex Quota Router 1.7.0

[中文](README.md) | **English**

Auditable routing recommendations for OpenAI Codex workflows, limited to GPT-6.2 Sol and GPT-6.2 Astra. A recommendation does not switch the running thread's model or prove that the target model executed.

| Model | Responsibility |
| --- | --- |
| GPT-6.2 Sol | Default execution at Low, Medium, or High effort as the task requires |
| GPT-6.2 Astra | Rare read-only architecture planning and root-cause diagnosis |

## Policies

- `balanced` (default): use score bands and hard risk gates to select the least expensive adequate route.
- `quality_first`: promote ordinary routes by one tier; preserve Sol High risk gates and the read-only Astra architecture role.
- `route_only`: return a recommendation and audit record without dispatching a worker.
- `subagents=auto|allow|deny`: control delegation separately; with `deny`, execute directly only if the current parent satisfies the selected route.
- Honor explicit model and effort choices. Validate effort against each model's capabilities; reject unknown models, combinations, and flags rather than silently downgrading. If an exact choice conflicts with a Sol High hard-risk gate, return a conflict instead of weakening the gate.

Model and effort combinations accepted by the offline router:

| Model | Supported effort |
| --- | --- |
| `gpt-6.2-sol`, `gpt-6.2-astra` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |

Default routing uses four roles. A parent on the selected model can act directly with adequate effort; explicit effort must match exactly. Cross-model substitution and explicit choices outside the allowlist are rejected. A valid choice still requires support from the execution host.

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

The installers archive retired managed profiles under `~/.codex/codex-quota-router-retired/`. The two-model limit applies to this skill and its managed roles; the installers do not change the model picker, provider catalogs, account entitlements, or `config.toml`. The old cross-model reuse arguments and audit field no longer apply.

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
- `agents/*.toml` — the four default role profiles.
