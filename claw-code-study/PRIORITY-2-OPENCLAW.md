# 优先级2：OpenClaw 增强方案（基于 claw-code 模式）

## 现状评估：OpenClaw 已高度吻合 claw-code 架构

| claw-code 概念 | OpenClaw 已有实现 | 评价 |
|---------------|------------------|------|
| Bootstrap Graph | AGENTS.md 启动顺序（步骤1-9） | ✅ 已有，但非显式DAG |
| PortContext | workspace 文件集（SOUL/IDENTITY/USER等） | ✅ 已有，但不统一 |
| 第一层（身份） | SOUL.md + IDENTITY.md + USER.md | ✅ 完整 |
| 第二层（操作） | AGENTS.md + HEARTBEAT.md | ✅ 已有 |
| 第三层（知识） | MEMORY.md + memory/ + shared-context/ | ✅ 完整 |
| ExecutionRegistry | skills/ 目录 | ⚠️ 有，但缺乏统一注册表 |
| Mode Routing | channel 多通道（feishu/telegram等） | ✅ 已有 |
| cost_tracker | session_status | ✅ 已有 |
| hooks | （待补充） | ❌ 空白 |

**结论：OpenClaw 底层架构比 claw-code 当前的 Python 实现更完整！**

---

## 具体可落地的增强

### 增强1：显式 Bootstrap Graph DAG（高优先级）

**现状：** AGENTS.md 的步骤是线性列表，没有描述依赖关系和条件分支。

**改进方案：** 在 AGENTS.md 中增加 `## Bootstrap Stages` 章节，显式建模：
```
Stage 1 → 身份加载（SOUL → IDENTITY → USER）
Stage 2 → 上下文加载（THESIS → FEEDBACK-LOG → SIGNALS → course-principles）
Stage 3 → 记忆加载（today + yesterday 日志）→ 仅 main session 加 MEMORY
Stage 4 → 健康检查（HEARTBEAT.md 规则）
```

### 增强2：PortContext 统一上下文对象（中等优先级）

**现状：** 各文件独立存在，没有统一的"当前状态摘要"。

**改进方案：** 增加 `PORT_CONTEXT.md`，作为当前会话的全局状态快照：
```markdown
# PORT_CONTEXT.md（自动生成，每次启动更新）

## 当前会话
- session_key: agent:main:feishu:direct:ou_xxx
- channel: feishu
- model: minimax-portal/MiniMax-M2.7
- last_active: 2026-03-31T15:00:00+08:00

## 今日记忆摘要
<!-- 由 memory/YYYY-MM-DD.md 自动提炼 -->

## 待关注事项
<!-- 从 HEARTBEAT.md 读取 -->
```

### 增强3：Skills ExecutionRegistry（高优先级）

**现状：** skills/ 目录下有大量 skill，但缺乏统一的注册表。

**改进方案：** 增加 `skills/REGISTRY.md`，显式列出：
- 各 skill 的功能分类（效率/信息/沟通/分析）
- 依赖关系（哪些 skill 依赖其他 skill）
- 优先级（主session vs 子agent）

### 增强4：Heartbeat 分层（低优先级，可实现）

**现状：** HEARTBEAT.md 内容扁平，所有检查混在一起。

**改进方案：** 参考 claw-code 的 Bootstrap Graph，给心跳增加分层：
```
Heartbeat Layer 1（快速）：HEARTBEAT_OK 检查
Heartbeat Layer 2（标准）：邮件+日历+天气
Heartbeat Layer 3（深度）：记忆整理+知识更新
```

---

## 可立即实施的改动（不依赖代码修改）

1. ✅ **更新 AGENTS.md** 增加 Bootstrap Graph DAG 章节
2. ✅ **增加 PORT_CONTEXT.md** 作为运行时状态快照
3. ✅ **增加 skills/REGISTRY.md** 统一 skill 注册表
4. ✅ **更新 HEARTBEAT.md** 增加分层结构

---
