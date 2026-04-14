# 优先级3：claw-code 架构 × 太擎产品 对照分析

## 太擎现有产品体系

| 产品 | 定位 | 状态 |
|------|------|------|
| 太擎大模型平台 | 行业模型 + 低代码开发底座 | 运营中 |
| 四大智能体矩阵 | 营销、电商、全球贸易、金融财税 | 已发布 |
| 旷湖数据云底座 | 训练数据供给 | 运营中 |
| 三层文件记忆架构 | 多Agent协作专利技术 | 专利申请中 |

---

## 核心发现：太擎三层架构 ≈ claw-code Harness

```
claw-code                        太擎三层架构
─────────────────────────────────────────────────────
Bootstrap Graph (DAG 7阶段)   ≈  第二层：操作层（AGENTS.md）
ExecutionRegistry               ≈  第一层：身份层（角色定义）
PortContext                     ≈  第三层：知识层（MEMORY.md）
Mode Routing (6种连接模式)       ≈  智能体路由分发（四大矩阵）
cost_tracker + hooks            ≈  （待补充）
```

**结论：** 太擎的三层架构和 claw-code 的 Harness 设计思路高度吻合，说明太擎的技术方向踩在了正确的大方向上。

---

## 具体对照分析

### 第一层：身份层
| claw-code | 太擎 | 对应关系 |
|-----------|------|----------|
| `assistant/` (Agent定义) | 四大智能体矩阵 | 不同行业Agent |
| `source_hint` (来源标记) | 智能体来源标识 | 一致 |
| `MirroredCommand` | 智能体技能 | 功能类似 |

**太擎可补充：** Agent 应该有 `source_hint`（来源行业/场景），便于精准路由。

### 第二层：操作层
| claw-code | 太擎 | 对应关系 |
|-----------|------|----------|
| Bootstrap Graph | AGENTS.md 启动流程 | 架构思想一致 |
| Trust Gate | （需补充安全校验） | 太擎空白 |
| Mode Routing | 智能体矩阵路由 | 太擎空白 |

**太擎可补充：** 
- Agent 的启动应该有显式的 trust gate（数据权限确认）
- Mode routing 可以让不同行业的智能体走不同连接路径

### 第三层：知识层
| claw-code | 太擎 | 对应关系 |
|-----------|------|----------|
| `PortContext` | MEMORY.md + memory/ | 功能类似 |
| `archive_available` 检查 | 知识积累 | 太擎已有 |
| Subsystem JSON | 行业知识包 | 太擎可抽象 |

**太擎可补充：**
- 类似 `PortContext` 的统一上下文对象，封装当前任务状态
- `archive_available` → 可以做"历史经验可用性"检查

---

## 给太擎的具体建议

### 建议1：引入 Mode Routing 思想
claw-code 的 6 种连接模式（local/remote/ssh/teleport/direct-connect/deep-link）可以让四大智能体矩阵支持多种部署场景：
- 营销Agent：本地部署（数据安全）
- 电商Agent：远程API调用（SaaS模式）
- 全球贸易Agent：深度链接嵌入（嵌入企业系统）

### 建议2：引入 ExecutionRegistry 统一管理技能
目前四大智能体是"整体"，建议在太擎平台内部建立：
- 技能注册表（哪些能力来自哪个Agent）
- 动态发现机制（新Agent上线自动注册）
- 依赖关系管理

### 建议3：引入 Bootstrap Graph 的分阶段启动
太擎三大层（身份/操作/知识）的加载顺序如果能像 claw-code 那样显式建模：
1. 先加载身份（谁在运行）
2. 再加载操作规则（允许做什么）
3. 最后加载知识（有什么积累）

可以减少初始化时的竞态条件和安全隐患。

### 建议4：在专利基础上增加 Mode Routing 权利要求
三层架构专利已申请，建议补充「第四层：路由层」的权利要求，涵盖多连接模式的智能分发逻辑。
