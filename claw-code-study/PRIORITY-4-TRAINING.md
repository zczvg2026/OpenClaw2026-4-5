# 优先级4：团队技术内部分享材料
> 可直接用于太擎/探迹团队内部分享

---

# 《Claude Code 源码泄露事件 + Harness 架构解读》

## 分享时长：30分钟 | 受众：技术团队 | 难度：中级

---

## 一、发生了什么（5分钟）

**2026年3月31日，北京时间下午4点23分**

- Anthropic 官方 Claude Code 的 npm 包中，source map 文件意外暴露了完整 TypeScript 源码
- @Fried_rice（Chaofan Shou）在 X 发布，24小时内：
  - **1358万观看**
  - **7380转帖**
  - **25784喜欢**
- 当晚 4AM，@instructkr 熬夜用 Python 从零干净重写，发布 `claw-code`

**一句话总结：** 一次意外泄露 → 一次开源社区的快速响应 → AI Agent Harness 架构首次被开源社区完整研究

---

## 二、什么是 Harness（10分钟）

**类比：**
> Harness = 攀岩时的安全带
> AI模型 = 攀岩者本人
> 工具 = 攀岩装备
> Harness 不让人掉下去，也不让人乱来

**Claude Code 的 Harness 做了什么：**

```
用户: "帮我把这个API接上"
    ↓
Bootstrap Graph（7阶段启动）
    ↓
ExecutionRegistry（查有哪些工具可用）
    ↓
PortContext（了解当前项目结构）
    ↓
Query Engine（解析用户意图）
    ↓
Tool Execution（执行具体操作）
    ↓
cost_tracker（记录花了多少token）
    ↓
结果反馈给用户
```

**为什么这重要：**
- 模型能力差距越来越小（Harness成为差异化）
- Claude Code 强不是因为模型，而是因为 harness
- OpenClaw / 太擎的架构选择直接影响产品竞争力

---

## 三、关键技术点详解（10分钟）

### 3.1 Bootstrap Graph — 分阶段安全启动

```
Stage 1: 全局初始化
Stage 2: 安全检查（环境/警告）
Stage 3: CLI解析 + 信任校验 ← 关键！
Stage 4: 命令+Agent 并行加载
Stage 5: 通过trust gate后延迟初始化
Stage 6: 路由（本地/远程/SSH/直连）
Stage 7: 查询循环
```

**关键设计：** Trust Gate 在 Stage 3，不是 Stage 7！
→ 越早排除危险，越安全

### 3.2 ExecutionRegistry — 工具的统一注册表

```
注册表:
  命令: Read/Edit/Bash/Glob/Web/Search...
  工具: TodoWrite/NotebookEdit/Browser...
  
每个工具/命令都有:
  - name（唯一标识）
  - source_hint（来自哪里）
  - handled（是否被执行）
```

**类比：** 像一个餐厅菜单 + 后厨系统
- 用户点菜（query）
- 前台查菜单（Registry）
- 后厨按标准做（mirrored execution）
- 每一道菜可追溯（execution record）

### 3.3 太擎三层架构 ≈ Claude Code Harness

| Claude Code | 太擎 | 说明 |
|-------------|------|------|
| Bootstrap Graph | AGENTS.md 启动 | 一致 |
| ExecutionRegistry | 四大智能体矩阵 | 类似 |
| PortContext | MEMORY.md + shared-context | 太擎更强 |

**太擎实际上已经在做 Claude Code 正在做的事！** 而且多了持久记忆。

---

## 四、我们能做什么（5分钟）

### 短期（1-2周）：
- [ ] 把这套架构语言纳入产品设计文档
- [ ] 在三层架构专利基础上补充 Mode Routing 权利要求
- [ ] 四大智能体矩阵引入工具注册表思维

### 中期（1个月）：
- [ ] OpenClaw 增加 Bootstrap Graph DAG 显式建模
- [ ] 太擎平台增加 Trust Gate（数据权限确认）
- [ ] 对标 Cline 的 MCP 协议支持

### 长期（3个月）：
- [ ] 实现 Mode Routing（四大矩阵 × 6种连接模式）
- [ ] 成为国内最完整的 Agent Harness 平台

---

## 五、讨论题

1. 我们的四大智能体矩阵，如何设计工具注册表？
2. Trust Gate 在企业场景应该如何落地？
3. 太擎的"记忆积累" vs Claude Code 的"无记忆"，哪个方向对？为什么？
