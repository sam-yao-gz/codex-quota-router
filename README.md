# Codex Quota Router v1.3.0

[中文](README.md) | [English](README_EN.md)

面向 OpenAI Codex 工作流的 quota-first 路由技能。默认优先使用 Luna；只有在证据支持时才升级到 Terra，Sol 仅用于少量架构级规划。默认并发为 1：一个任务交给一个 worker。

```text
任务 → quota-first 决策 → Luna
                         │ 不可用 / 命中硬门槛
                         ▼
                       Terra →（少量）Sol
```

## 为什么使用

- 将路由建议、实际执行和 effective model 证据分开，避免把标签当成执行证明。
- 避免重复 worker，同时保留有边界的 Luna → Terra 可用性回退。
- 明确表达 unavailable、transport/TLS 和 metadata unknown，不用猜测补齐状态。

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
- `Use Luna only`：禁用可用性回退，Luna 无法启动时报告阻塞。
- `Route only`：只输出路由建议，不执行 worker。
- `Do not use subagents`：留在当前线程，并将结果标为建议。

### 6. 验证 / 卸载

运行结构校验：

```bash
python scripts/validate_skill.py
```

卸载：Windows 运行 `powershell -ExecutionPolicy Bypass -File .\uninstall.ps1`；Linux/macOS 删除已安装的 skill 和 agent 文件，并在安装器修改过全局 `AGENTS.md` 时恢复备份。

## v1.3.0 亮点

- 300 秒 half-open lease，并可回收过期 probe。
- 使用业务任务 recovery probe，而不是 health-only worker。
- 当当前模型与 effort 已满足路由时允许 parent reuse。
- 默认并发为 1，保持一任务一 worker。
- 复用已有验证，减少重复工作。
- Transport/TLS 故障与模型不可用保持独立。
- 提供真实 effective-model 审计字段；路由标签本身不是执行证据。

## 设计与开发文件

- `SKILL.md`：路由、quota-first 可用性控制器和执行约定。
- `references/execution-contract.md`：执行状态与回退边界。
- `references/routing-policy.md`：评分与硬门槛。
- `scripts/route_score.py`：确定性路由评分与回退模拟。
- `agents/*.toml`：固定模型与 effort 配置。
