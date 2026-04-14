---
scope: team
---

# Claude Code 源码 + 泄露分析笔记

> 来源：~/Desktop/zczvg/claude-code-complete/（1423个.ts，184MB）
> 参考：微信公众号文章《AI大牛必读：Claude Code 泄露的512K行代码里藏着什么》
> 时间：2026-04-04

## 核心结论

**Harness 决定性能差距**：同一模型，Claude Code harness 得 78%，其他框架 42%。工具本身不值钱，Harness 才值钱。

## 架构亮点

### 记忆系统（与我们高度相似）
- 4类型 taxonomy：user / feedback / project / reference（与我们的体系完全一致）
- extractMemories：每轮结束后触发，cursor 断点增量提取
- autoDream：24h + 5会话门控，fork 子 agent 整合
- 格式：frontmatter + **Why:** + **How to apply:**
- **差异**：Claude Code 有 prompt 缓存 fork（零开销创建子会话），我们尚无

### 权限分类引擎（⭐⭐⭐⭐⭐ 最值钱模块）
- 工具按风险分级：read-only / write / destructive
- 每步操作前有审批流程（企业级核心）
- AgentTool 目录包含完整权限抽象层

### Context 管理
- autoCompact：自动压缩
- reactive compact：响应式压缩
- memory 双层：private vs team（与本次 scope-design 一致）

### 其他
- session 状态机：bootstrap/state.ts 完整 8 个状态流转
- Tools 抽象：工具注册 → 执行 → 权限校验完整链路
- hooks 系统：pre/post 钩子注入点完整

## 我们可优化的方向

| 优先级 | 优化项 | 状态 |
|--------|--------|------|
| P0 | 权限分级确认机制 | ✅ 2026-04-04 设计完成 |
| P1 | private vs team 双层记忆 | ✅ 2026-04-04 实施完成 |
| P2 | fork subagent 模式（Dream 期间不阻塞主会话） | 待做 |
| P2 | Feature Flag 框架 | 待做 |

## 源码关键文件路径
- 记忆服务：`src/services/autoDream/`、`src/services/extractMemories/`
- 权限系统：`src/tools/AgentTool/`
- 状态机：`src/bootstrap/state.ts`
- 核心 agent：`src/coordinator/`、`src/buddy/`
- memory 类型：`src/memdir/memoryTypes.ts`（与我们的 taxonomy 完全一致）
