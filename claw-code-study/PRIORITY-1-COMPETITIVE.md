# 优先级1：AI Coding Agent 竞品技术分析

## 市场格局概览

### 主要玩家

| 产品 | 开发商 | 定位 | 核心特点 |
|------|--------|------|----------|
| **Claude Code** | Anthropic | AI编程旗舰 | 首个商业级harness，生态最完整 |
| **Cline** | /cline-ai | 开源社区王 | VS Code扩展，免费可定制 |
| **Cursor** | Anysphere | AI IDE | 深度IDE集成，协作友好 |
| **Roo Code** | /roo-build | 自动驾驶 | 高度自动化，减少人工干预 |
| **OpenClaw** | OpenClaw社区 | Agent平台 | 多channel，记忆架构 |
| **claw-code** | instructkr | 架构研究 | Harness开源重实现 |

---

## 技术架构对比

### 1. Claude Code（原始 + 泄露源码）

**架构亮点：**
- **Bootstrap Graph** — 7阶段DAG启动，分离trust gate
- **ExecutionRegistry** — 命令/工具统一注册，支持mirrored执行
- **Mode Routing** — 6种连接模式（local/remote/ssh/teleport/direct/deep-link）
- **PortContext** — 项目结构抽象层
- **cost_hook** — token消耗实时监控

**护城河：**
- 品牌 + 生态（Anthropic API绑定）
- 深度集成 Anthropic 模型优化
- 完整的工具链（gitlab/github/terminal）

### 2. Cline（开源代表）

**架构特点：**
- 纯 VS Code 扩展，local-first
- MCP（Model Context Protocol）支持好
- 社区驱动，工具生态丰富
- 工具执行需用户确认（安全但慢）

**优势：**
- 免费，开源可审计
- 高度可定制
- 社区插件生态

**劣势：**
- 依赖VS Code，不够泛化
- 无记忆积累能力（每次会话独立）
- 无Mode Routing（单一本地模式）

### 3. Cursor（AI IDE代表）

**架构特点：**
- 基于 Composer 的多文件编辑
- 深度IDE集成（自动补全/导航/refactor）
- Rule-based agent 模式
- 支持 Agent Mode

**优势：**
- 最好的代码补全体验
- 实时协作
- 团队共享规则

**劣势：**
- 记忆能力弱（基于当前项目）
- 封闭生态

### 4. Roo Code（自动驾驶代表）

**架构特点：**
- 高自动化程度（Auto-approve 能力）
- 支持多模型并行
- 任务分解 + 自动执行
- 简单任务几乎无需人工介入

**优势：**
- 最低人工干预
- 多模型竞争选择

**劣势：**
- 高风险操作缺乏足够校验
- 企业场景合规性弱

---

## Harness 架构能力对比

| 能力维度 | Claude Code | Cline | Cursor | Roo Code | OpenClaw |
|----------|------------|-------|--------|----------|----------|
| 工具注册中心 | ✅ Registry | ✅ MCP | ⚠️ 有限 | ✅ | ⚠️ Skill |
| 启动DAG | ✅ 7阶段 | ❌ 线性 | ❌ 线性 | ❌ 线性 | ⚠️ 有序列表 |
| 记忆积累 | ⚠️ 会话级 | ❌ | ⚠️ 项目级 | ❌ | ✅ 三层文件 |
| Mode路由 | ✅ 6种 | ❌ | ❌ | ❌ | ✅ 多channel |
| 成本追踪 | ✅ | ❌ | ✅ | ❌ | ✅ |
| Trust Gate | ✅ | ⚠️ 用户确认 | ⚠️ 用户确认 | ⚠️ 自动批准 | ⚠️ 待增强 |
| 开放架构 | ❌ | ✅ | ❌ | ❌ | ✅ |

---

## 关键洞察

### 洞察1：Harness 是核心差异化
所有 AI Coding 工具的模型都差不多（Claude/GPT4），真正的差异在于：
- 工具编排能力（多少工具、如何组合）
- 启动和初始化流程（安全 + 效率）
- 上下文管理（记忆能否积累）

**claw-code 的价值：** 第一次把 Claude Code 的 harness 变成了开源可研究的东西

### 洞察2：Mode Routing 是下一个大方向
Claude Code 的 6 种连接模式目前只有官方实现了 local/ssh/direct-connect，其他都还在开发。这说明：
- 未来的 Agent 不只是"在本地跑"，而是"可以在任何环境下跑"
- Mode Routing 是让 AI Agent 泛化能力的关键

### 洞察3：三层架构 = 企业级门槛
OpenClaw 和太擎的三层架构（身份/操作/知识）是真正企业级方案的前提：
- Cline/Roo Code 缺乏身份层 = 无法做多角色权限
- Claude Code 有身份但不开源
- 太擎专利覆盖 = 护城河

### 洞察4：记忆积累是护城河
Claude Code / Cline / Roo Code 都是"每次从零开始" → OpenClaw 和太擎的持久记忆是真正的差异化能力

---

## 对太擎的建议

1. **Mode Routing** 应该纳入四大智能体矩阵的架构设计
2. **记忆积累** 是太擎对比 Cline/Roo Code 的核心优势，应该放大
3. **三层架构专利** 是战略资产，建议在出海前完成PCT国际申请
4. **工具注册中心** 可以借鉴 ExecutionRegistry 的设计思想
