# Codex Quota Router 1.4.2-local

委派 worker 默认不得再派生 descendant；若需要更深委派，会以 blocked/escalation 返回父线程，不创建第二个 worker。

[中文](README.md) | [English](README_EN.md)

<p align="center"><img src="assets/codex-quota-router-hero.png" alt="Codex Quota Router model routing overview"></p>

为 OpenAI Codex 工作流提供模型路由建议：默认优先 GPT-6 Luna，按风险建议 GPT-6.1 Sol，架构规划才考虑 GPT-6 Astra。路由建议不代表当前线程可切换模型，也不代表模型已经执行。

| 模型 | 职责 |
| --- | --- |
| Luna | 默认的低额度、高性价比执行 |
| Sol | 风险硬门槛、隐藏耦合与推理升级 |
| Astra | 少量架构级规划与根因诊断 |

```text
任务 → quota-first 决策 → Luna
                         │ 风险 / 复杂度门槛
                         ▼
                       Sol →（少量）Astra
```

## 为什么使用

- 将路由建议、实际执行和 effective model 证据分开，避免把标签当成执行证明。
- 只按风险、复杂度和用户明确偏好升级到 Sol，不根据 Luna 启动失败自动换模。
- 将推荐路由、实际请求与运行时证据分开；Luna 执行失败时报告阻塞。

## 🚀 5 分钟上手

### 1. 安装

Windows：

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Linux/macOS：

```bash
chmod +x install.sh
./install.sh
```

若不希望修改全局路由文件，Windows 使用 `-SkipGlobalAutoRouting`，Linux/macOS 使用 `SKIP_GLOBAL_AUTO_ROUTING=1`。

### 2. 重启 Codex

安装完成后重启 Codex，使 skill、agent 配置和全局指令重新加载。

### 3. 正常使用

直接提交普通任务即可。路由器默认 quota-first，优先选择 Luna；不需要额外命令或服务。

### 4. 显式调用

在任务中明确写出你的约束，例如：`Use Luna only`、`Route only` 或 `Do not use subagents`。这些约束会覆盖相应的默认行为，并如实报告无法执行的情况。

### 5. 常用控制方式

- `Do not optimize quota`：允许质量优先升级。
- `Use Luna only`：坚持 Luna 路由；风险门槛要求其他模型时报告冲突。
- `disable_luna`（或“这次禁用 Luna”）：显式偏好 Sol；普通任务使用 Sol Medium，风险和架构门槛仍适用。
- `Route only`：只输出路由建议，不执行 worker。
- `Do not use subagents`：留在当前线程，并将结果标为建议。

### 6. 验证 / 卸载

运行结构校验：

```bash
python scripts/validate_skill.py
```

卸载：Windows 运行 `powershell -ExecutionPolicy Bypass -File .\uninstall.ps1`；Linux/macOS 删除已安装的 skill 和 agent 文件，并在安装器修改过全局 `AGENTS.md` 时恢复备份。

## 主要行为

- 仅在显式 opt-in、父线程 effort 足够且任务明确限于两文件或一个已知安全命令时，允许轻量 parent reuse；高风险和显式模型/effort 约束除外。
- Worker 数量按独立工作量决定，不设固定配额；通常 Low 为 0、Mid 为 0-1、High 为 0-2。
- 复用已有验证，减少重复工作。
- 提供真实 effective-model 审计字段；路由标签本身不是执行证据。
- Luna 无法启动或执行时报告阻塞，不自动分配 Sol。
- `disable_luna` 是独立的显式用户偏好：普通任务转 Sol Medium；风险和架构硬门槛仍分别使用 Sol High/Astra Medium。

若 `disable_luna` 与 `Use Luna only` 冲突，会报告冲突，不静默改选。

## 设计与开发文件

- `SKILL.md`：路由和执行约定。
- `references/execution-contract.md`：执行状态与失败处理。
- `references/routing-policy.md`：评分与硬门槛。
- `scripts/route_score.py`：确定性路由评分与直接复用决策。
- `agents/*.toml`：固定模型与 effort 配置。
