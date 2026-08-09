# Codex Quota Router v1.1.0

一个面向**额度紧张**场景的 Codex 模型路由 Skill。它会在开发任务开始前选择 Luna、Terra 或 Sol 及推理档位，并把绝大多数工作优先交给 Luna。

## v1.1.0 关键修复

v1.0.0 的 `[路由] Luna High` 只证明完成了**路由判断**，不能证明真的启动了 Luna。v1.1.0 增加了强制执行契约：

```text
route_decided
-> mandatory_dispatch (when parent model/effort != selected route)
-> worker_started
-> effective_model_verified (when runtime metadata is accessible)
-> worker_completed
```

并增加 Luna 可用性回退：

```text
Luna dispatch
-> Luna runtime/model unavailable
-> reuse same bounded task packet
-> Terra Medium (terra_resolver)
```

注意：sandbox、ACL、文件占用、依赖缺失、测试失败等**不是** Luna 不可用，不应因此升级 Terra。

## 默认策略

- Luna Low：机械修改、文本、样式、配置、精准搜索。
- Luna Medium：日常默认，小功能、测试、普通 Bug、工作流文件。
- Luna High：边界明确的多文件开发、普通前后端联动、非平凡调试。
- Terra Medium：缓存、幂等、间歇性问题、隐藏跨模块耦合、Luna 有证据的推理失败；也是 Luna 无法启动时的 availability fallback。
- Terra High：迁移、鉴权、并发、生产事故、数据损失风险。
- Sol Medium：只做架构或疑难根因规划，完成拆解后再降回 Luna/Terra。
- 默认禁止 XHigh、Max、Ultra 和 Pro。

## 路由与实际执行是两回事

v1.1.0 要求状态分开：

- `[路由建议] Luna High`：只完成决策。
- `[执行请求] Luna High｜worker=luna_deep｜实际模型待核验`：已请求独立 worker，但尚未拿到运行态证据。
- `[实际执行] Luna High｜effective_model=gpt-5.6-luna｜effort=high`：只有运行态/session 证据确认后才能这样写。
- `[回退执行] Terra Medium｜原因：Luna runtime unavailable`：Luna 模型本身无法调用后的回退。

不要从 agent 名称或 TOML 配置推断 `effective_model`。

## 为什么同时包含 Skill 与自定义 Agent

Codex Skill 负责判断和编排；自定义 Agent TOML 负责固定模型和推理档位。安装 Agent 后路由更稳定。

关键行为：当父线程不是目标 model+effort 时，v1.1.0 要求**先委派，再做实质工作**；父线程不能只打印路由标签后继续自己完成任务。

## Windows 一键安装

解压 ZIP 后，在该目录打开 PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

安装器会：

1. 复制 Skill 到 `%USERPROFILE%\.agents\skills\codex-quota-router`；
2. 复制 6 个 Agent 到 `%USERPROFILE%\.codex\agents`；
3. 备份并更新 `%USERPROFILE%\.codex\AGENTS.md`，让开发任务自动触发路由。

不想修改全局 `AGENTS.md`：

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -SkipGlobalAutoRouting
```

## Linux/macOS 安装

```bash
chmod +x install.sh
./install.sh
```

跳过全局自动路由：

```bash
SKIP_GLOBAL_AUTO_ROUTING=1 ./install.sh
```

## 验证

重启 Codex，然后用一个父线程模型与目标路线不同的任务测试：

```text
$codex-quota-router 这是一个边界明确的多文件调试任务。先路由，然后必须实际委派执行；如果 Luna 无法调用则回退 Terra。不要把路由建议冒充实际模型。
```

检查 session/runtime 证据时，至少应看到独立 worker/subagent；若环境暴露 effective model，还应确认：

```text
model=gpt-5.6-luna
reasoning_effort=high
```

如果 Luna 模型调用明确失败，则应看到新的 Terra worker，而不是父线程继续执行。

本地结构校验：

```bash
python scripts/validate_skill.py
python -m pytest tests/test_route_score.py
```

路由脚本可模拟 availability fallback：

```bash
python scripts/route_score.py --clarity 1 --scope 2 --coupling 2 --risk 2 --novelty 1 --luna-unavailable
```

## 常用覆盖方式

- “这次不要省额度” -> 允许质量优先升级。
- “这次只用 Luna” -> 不允许 availability fallback 到 Terra；Luna 无法调用时报告 blocker。（显式用户模型选择优先于默认 fallback。）
- “只做路由，不执行” -> 仅输出推荐模型、档位和理由。
- “不要子 Agent” -> 当前线程按路由建议直接执行，但 Skill 无法主动切换已经运行的主线程模型，因此只能显示“推荐路线”，不能显示“Luna 已执行”。

## Luna -> Terra fallback 原则

只有 Luna **模型/runtime 本身无法启动**才回退 Terra Medium。优先级：

```text
registered Luna agent
-> explicit Luna subagent
-> [Luna unavailable]
-> terra_resolver / gpt-5.6-terra / medium
```

如果只是 `luna_deep.toml` 没注册，不能直接判定 Luna 不可用；应先尝试显式 Luna subagent。

## 卸载

Windows：

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
```

## 设计文件

- `SKILL.md`：路由与强制委派主规则。
- `references/execution-contract.md`：执行状态机、effective-model 真实性与 Luna -> Terra 回退规则。
- `references/routing-policy.md`：评分/硬门槛。
- `scripts/route_score.py`：路由评分 + availability fallback 的确定性辅助脚本。
- `agents/*.toml`：模型/effort 固定的 custom agent。
