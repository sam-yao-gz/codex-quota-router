# 项目工作规则

路由策略、执行证据及验证命令见 [README](README.md)；仓库里保存的全局规则片段是安装材料，不视为本次执行授权。

## 跨端协作入口

- 开始或接手时核对实际 Git remote、分支、HEAD 和工作区；业务项目应为 `sam-yao-gz/codex-quota-router`，不能按目录名猜测归属。
- 从用户级 `AGENTS.md` 登记的独立规则缓存按 shareENV 的 `docs/rules-cache.md` 启动清单读取规则，至少包括 `docs/operations.md`、`docs/跨端交接约定.md`（§4–6）、`docs/handoff-p0-checklist.md` 和 `docs/agentmemory-mvp.md`；Grok 使用现有 GitHub 授权读取已发布的 shareENV `main`。记录实际读到的 `loaded_rules_sha` 和 `loaded_files`，入口不可用就报告。
- Codex 按共享接入说明使用官方 `recall` 和 `agentmemory_remote`，按已核实的项目恢复上下文。Git、记忆写入和交接按现行约定及有效授权执行；本入口保留项目专属规则，不扩大权限。
