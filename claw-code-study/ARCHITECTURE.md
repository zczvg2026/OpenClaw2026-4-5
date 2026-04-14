# CLAW-CODE 架构学习笔记
> 来源：instructkr/claw-code (GitHub)
> 学习日期：2026-03-31
> 背景：Claude Code 源码泄露事件后，instructkr 于 2026-03-31 当天完成 Python Clean-Room 重写

---

## 一、整体定位

**一句话定义：**
Claude Code Agent Harness 的 Python Clean-Room 重实现 + 架构研究项目。

**不是：** 一个能直接运行的完整产品
**是：** 一套 harness（工具编排层）的架构蓝图 + 早期 Python 骨架

---

## 二、核心架构：Bootstrap Graph（启动图）

Claude Code 的启动流程被建模为一个 **有向无环图（DAG）**，共 7 个阶段：

```
1. top-level prefix side effects        ← 全局初始化副作用
2. warning handler + env guards          ← 警告处理 + 环境安全检查
3. CLI parser + pre-action trust gate    ← CLI 解析 + 预操作信任校验
4. setup() + commands/agents parallel load   ← 并行加载命令+Agent
5. deferred init after trust             ← 信任验证后的延迟初始化
6. mode routing                         ← 模式路由（见下方）
7. query engine submit loop              ← 查询引擎提交循环
```

**模式路由（Mode Routing）** 支持 6 种连接模式：
- `local` — 本地直接运行
- `remote` — 远程连接
- `ssh` — SSH 隧道
- `teleport` — 穿透连接
- `direct-connect` — 直连
- `deep-link` — 深度链接调用

---

## 三、核心模块详解

### 3.1 命令编排层（commands.py）
```python
@dataclass
class CommandExecution:
    name: str
    source_hint: str   # 来源：哪个原始模块
    prompt: str
    handled: bool
    message: str

# 核心函数
load_command_snapshot()       # 从JSON加载所有命令元数据
get_command(name)              # 按名称查询单条命令
find_commands(query)           # 模糊搜索命令
execute_command(name, prompt)  # 执行镜像命令
```

**设计思想：** 命令不是硬编码，而是从 `reference_data/commands_snapshot.json` 动态加载，支持按 source_hint 过滤（如排除 plugin/skill 相关命令）。

### 3.2 工具编排层（tools.py / execution_registry.py）
```python
@dataclass
class MirroredTool:
    name: str
    source_hint: str

@dataclass
class MirroredCommand:
    name: str
    source_hint: str

class ExecutionRegistry:
    commands: tuple[MirroredCommand, ...]
    tools: tuple[MirroredTool, ...]
    
    def command(name) -> MirroredCommand | None
    def tool(name) -> MirroredTool | None
```

**设计思想：** 工具和命令统一注册表，通过名称进行 O(1) 查询，支持动态注入。

### 3.3 上下文管理层（context.py）
```python
@dataclass
class PortContext:
    source_root: Path      # src/ 源码目录
    tests_root: Path       # tests/ 测试目录
    assets_root: Path       # assets/ 资源目录
    archive_root: Path      # reference_data/claude_code_ts_snapshot/src/
    python_file_count: int
    test_file_count: int
    asset_file_count: int
    archive_available: bool  # 泄露代码是否在本地存在
```

**设计思想：** 上下文对象将项目结构和源码审计能力封装在一起，支持条件逻辑（archive_available 决定是否做代码对比）。

### 3.4 协调器（coordinator/）
负责多子系统协调，目前结构已建立，功能为占位符。

### 3.5 辅助子系统
| 模块 | 作用 |
|------|------|
| `assistant/` | Agent 行为定义 |
| `bridge/` | 与原版 Claude Code 的桥接层 |
| `buddy/` | Buddy 伙伴系统（任务伙伴） |
| `hooks/` | 生命周期钩子（cost hook 等） |
| `cost_tracker.py` | Token 消耗追踪 |
| `direct_modes.py` | 直接模式定义 |
| `history.py` | 对话历史管理 |
| `ink.py` | 终端输出美化 |
| `interactiveHelpers.py` | 交互式辅助函数 |

---

## 四、Subsystem 架构（基于 JSON 描述文件）

每个 subsystem 有独立的 JSON 描述：
- `archive_name` — 原始名称
- `module_count` — 包含模块数
- `sample_files` — 示例文件列表

这使得可以用 LLM 自动分析和比较 subsystem 之间的差异。

---

## 五、与 OpenClaw 的架构对比

| 维度 | OpenClaw | claw-code |
|------|----------|-----------|
| 核心理念 | Agent 平台（多 channel） | 单 Agent 编程工具 |
| 工具注册 | Skill 系统（动态加载） | ExecutionRegistry（静态 JSON） |
| 启动管理 | Gateway 启动 | Bootstrap Graph DAG |
| 上下文 | workspace 多文件 | PortContext 路径封装 |
| 模式路由 | channel 多通道 | Mode Routing（6种连接模式） |
| 成本追踪 | 已有（session_status） | cost_tracker + costHook |

---

## 六、关键设计模式

### 6.1 Mirror Pattern（镜像模式）
不直接执行操作，而是通过"镜像"层：
- `MirroredCommand` / `MirroredTool` 包装原始实现
- 支持延迟加载、权限控制、日志记录
- 使得替换底层实现而不影响上层调用

### 6.2 Deferred Init Pattern（延迟初始化）
```
Bootstrap Graph Stage 4 → Stage 5 之间
trust gate 通过后才执行敏感初始化
```
安全关键操作分两步走，减少攻击面。

### 6.3 Query Engine Pattern（查询引擎）
最后阶段启动"查询引擎提交循环"：
- 用户 query → 解析 → 路由 → 执行 → 反馈 → 循环
- 类似 ReAct 模式，但更结构化

### 6.4 Port Context Pattern
用 `PortContext` 将项目物理结构抽象为统一接口：
- 代码量统计
- 路径解析
- archive 对比能力

---

## 七、参考价值

### 可借鉴到 OpenClaw 的设计：
1. **Bootstrap Graph** → OpenClaw 的 skill 加载可以用 DAG 描述依赖顺序
2. **PortContext** → 封装 workspace 上下文，供各个 skill 共享
3. **ExecutionRegistry** → 统一的工具/命令注册中心，比现有 skill 系统更结构化
4. **Deferred Init** → 敏感操作的延迟初始化可以增强 OpenClaw 安全

### 对太擎产品的参考：
1. 如果做 AI Coding 工具：命令/工具的镜像 + 注册模式是核心
2. 如果做 Agent 平台：Bootstrap Graph 的分阶段启动 + 模式路由是成熟方案
3. Subsystem JSON 描述文件 → 可用于 AI 产品自动化测试和对比分析
