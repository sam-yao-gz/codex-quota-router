# Codex Quota Router 1.7.0

[中文](README.md) | [English](README_EN.md)

为 OpenAI Codex 工作流提供可审计的路由建议，仅允许 GPT-6.2 Sol 和 GPT-6.2 Astra。路由建议不代表当前线程已切换模型，也不代表目标模型已经执行。

| 模型 | 职责 |
| --- | --- |
| GPT-6.2 Sol | 默认执行；按任务选择 Low、Medium 或 High |
| GPT-6.2 Astra | 少量只读架构规划与根因诊断 |

## 策略

- `balanced`（默认）：使用评分区间和风险硬门槛选择可完成任务的最低配置。
- `quality_first`：普通任务按一个档位提升；Sol High 风险门槛和 Astra 只读架构规划保持原有职责。
- `route_only`：只返回推荐与审计信息，不派发 worker。
- `subagents=auto|allow|deny`：单独控制委派倾向；`deny` 时，仅当当前父线程满足路由要求才直接执行。
- 用户明确指定的模型和 effort 优先保留。effort 按模型能力校验；未知模型、effort 组合或 flag 会明确报错。若精确选择与 Sol High 风险门槛冲突，也会报错而不降低门槛。

路由器离线接受的模型与 effort：

| 模型 | 支持的 effort |
| --- | --- |
| `gpt-6.2-sol`、`gpt-6.2-astra` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |

默认路由有四个角色。模型相同且 effort 足够的父线程可直接工作；明确指定的 effort 必须精确匹配。不允许用其他模型替代，也不允许显式选择名单外的模型。有效选择仍取决于执行端是否支持。

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

安装器会将其管理的旧角色移出 `~/.codex/agents`，归档到 `~/.codex/codex-quota-router-retired/`，不改变供应商或帐户权限。若不希望修改全局路由文件，Windows 使用 `-SkipGlobalAutoRouting`，Linux/macOS 使用 `SKIP_GLOBAL_AUTO_ROUTING=1`。安装完成后重启 Codex。

两模型限制作用于本 Skill 和它管理的角色，安装器不会修改模型选择器、外部模型目录或 `config.toml`。升级后，旧版跨模型复用参数及记录字段不再适用。

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
- `agents/*.toml`：四个默认角色的模型与 effort 配置。
