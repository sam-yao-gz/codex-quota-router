# Codex Quota Router 1.5.0

[中文](README.md) | [English](README_EN.md)

<p align="center"><img src="assets/codex-quota-router-hero.png" alt="Codex Quota Router model routing overview"></p>

为 OpenAI Codex 工作流提供可审计的模型路由建议：默认按任务匹配 GPT-6 Luna，风险和隐藏耦合任务使用 GPT-6.1 Sol，少数只读架构规划使用 GPT-6 Astra。路由建议不代表当前线程已切换模型，也不代表目标模型已经执行。

| 模型 | 职责 |
| --- | --- |
| Luna | 默认执行；按任务选择 Low、Medium 或 High |
| Sol | 高风险门槛、隐藏耦合与推理升级 |
| Astra | 少量只读架构规划与根因诊断 |

## 策略

- `balanced`（默认）：使用评分区间和风险硬门槛选择可完成任务的最低配置。
- `quality_first`：普通任务按一个档位提升；Sol High 风险门槛和 Astra 只读架构规划保持原有职责。
- `route_only`：只返回推荐与审计信息，不派发 worker。
- `subagents=auto|allow|deny`：单独控制委派倾向；`deny` 时，仅当当前父线程满足路由要求才直接执行。
- 用户明确指定的模型和 effort 优先保留。effort 按模型能力校验；未知模型、effort 组合或 flag 会明确报错。若精确选择与 Sol High 风险门槛冲突，也会报错而不降低门槛。

当前 Codex 主机暴露的显式 effort 能力：

| 模型 | 支持的 effort |
| --- | --- |
| `gpt-6-luna` | `none`, `low`, `medium`, `high`, `xhigh`, `max` |
| `gpt-6.1-sol` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| `gpt-6-astra` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |

默认路由仍使用已安装的六个 agent profile；显式更高 effort 只有在执行机制支持并实际传入时才生效。

## 安装

Windows：

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Linux/macOS：

```bash
chmod +x install.sh
./install.sh
```

若不希望修改全局路由文件，Windows 使用 `-SkipGlobalAutoRouting`，Linux/macOS 使用 `SKIP_GLOBAL_AUTO_ROUTING=1`。安装完成后重启 Codex。

## 验证

```bash
python scripts/validate_skill.py
python scripts/run_tests.py
```

路由评分 helper 可输出路由建议和审计字段。评分 helper 不派发 worker，也不能证明模型已执行；effective model/effort 仅在有运行时证据时填写。只有推理或逻辑失败会增加升级评分；依赖、权限、测试、网络和用户输入阻塞会分类记录，不触发模型升级。

卸载：Windows 运行 `powershell -ExecutionPolicy Bypass -File .\uninstall.ps1`；Linux/macOS 删除已安装的 skill 和 agent 文件，并在安装器修改过全局 `AGENTS.md` 时恢复备份。

## 设计文件

- `SKILL.md`：路由和执行约定。
- `references/execution-contract.md`：执行状态与失败处理。
- `references/routing-policy.md`：策略、评分、努力级别与风险硬门槛。
- `scripts/route_score.py`：确定性路由评分与策略校验。
- `agents/*.toml`：默认六个模型与 effort 配置。
