# Extract Skill 🦀🧠

## 与 Dream Skill 的关系

| | Dream（做梦） | Extract（提取） |
|--|-------------|----------------|
| 触发 | 每24小时 cron | 每30分钟 cron |
| 任务 | 深度整合、Prune、纠错 | 实时捕获新记忆 |
| 范围 | 全量记忆文件 | 仅新消息（相对上次） |
| 时效 | 深夜批处理 | 日常增量 |

两者互补：Extract 负责"进来"，Dream 负责"整理"。

## 触发时机

- cron：`every 30m`，在 07:00–23:00 之间
- 独立 isolated session，不打扰主会话
- cron id：`extract-realtime-memory`

## 核心机制

### 1. Cursor（断点）

存储在 `memory/.dream-lock.json` 里：
```json
{
  "dreaming": false,
  "lastDreamedAt": "...",
  "lastExtractedAt": "2026-04-02T07:00:00+08:00"
}
```

每次提取后更新 `lastExtractedAt`。

### 2. 新消息识别

读取当前会话 transcript（飞书主会话），过滤：
- 时间戳 > lastExtractedAt 的消息
- 排除自己的心跳消息（内容含 HEARTBEAT_OK 的）

### 3. 提取 prompt（4类记忆）

参考 Claude Code 的 taxonomy：

**user**：用户角色、偏好、背景
- 例："Johnson 出差常去杭州、上海" → user-johnson.md

**feedback**：对的工作+错的工作（含 Why）
- 例："太擎≠太驍，字不要写错" → key-lessons.md

**project**：项目进展、决策、截止日期
- 例："决定落地 extractMemories" → projects.md

**reference**：外部系统信息（工具配置、API路径）
- 例："IMA ClientID 是..." → 已存在则跳过

### 4. 工具约束

- Read/grep/glob：不限
- Bash：只读（ls/find/cat/stat/wc/head/tail）
- Edit/Write：只能写 memory/ 目录下的 .md 文件

### 5. 互斥检测

如果 Extract 执行期间，主 agent 写了记忆（通过检查 memory/ 目录的 mtime），则本次跳过，避免重复写入。

## 文件结构

```
workspace/
├── memory/
│   ├── .dream-lock.json     # 含 lastExtractedAt
│   └── *.md                # topic 文件
└── skills/extract-skill/
    └── EXTRACT_PROMPT.md
```

## ⚙️ 闭包状态管理

Extract 采用闭包封装临时状态，**不持久化**到磁盘：

```typescript
// 闭包内状态（不在文件里持久化）
let lastExtractTime: number | null = null
let inProgress = false
let pendingContext: { messages: Message[], sessionKey: string } | null = null

/**
 * 主入口：若 inProgress=true，stash pendingContext，不覆盖
 */
function extract(context: { messages: Message[], sessionKey: string }): void {
  if (inProgress) {
    // 正在执行中，暂存pending，不覆盖已有的pending
    if (!pendingContext) {
      pendingContext = context
    }
    return
  }
  inProgress = true
  pendingContext = context
  runExtract()
}

/**
 * 执行提取，完成后 inProgress=false，
 * 若有 pending 则立即触发新一轮
 */
async function runExtract(): Promise<void> {
  try {
    const ctx = pendingContext!
    pendingContext = null
    lastExtractTime = Date.now()
    // ... 执行提取逻辑
  } finally {
    inProgress = false
    // 有pending则立即再跑
    if (pendingContext) {
      runExtract()
    }
  }
}
```

**并发保护**：inProgress=true 时，新的 extract() 调用不覆盖已有的 pendingContext，保证不丢上下文，也不并发两个提取进程。

## 注意事项

- 只提取消息内容，不重复造轮子
- 发现重复 topic 直接更新，不创建新文件
- 输出：一句话摘要，不发飞书消息

## Context Compression（自动压缩）

当对话 token 接近 200k 限制时，自动触发上下文压缩。

### 触发阈值

- **警告阈值**：剩余 `< 20_000` tokens → 发飞书警告给用户
- **压缩阈值**：`effectiveContextWindow - 13_000` tokens 剩余时触发
- **强制压缩**：剩余 `< 5_000` tokens → 立即压缩，不等确认

### 熔断器

状态存 `memory/compaction_state.json`：

```json
{
  "consecutiveFailures": 0,
  "lastFailureAt": null,
  "circuitOpen": false
}
```

- 每次 compaction 失败：`consecutiveFailures++`
- 成功：重置为 0
- `consecutiveFailures >= 3`：停止自动压缩，circuitOpen=true
- 通知用户："context 压缩连续失败3次，已暂停自动压缩，请手动处理或重启 session"
- 熔断打开后需人工介入（删除 compaction_state.json 或手动重置）才恢复

### 压缩原则

**保留：**
- 核心主题和目标
- 用户偏好和习惯
- 待办事项和约定
- 重要结论和决定
- 关键信息和数据

**压缩：**
- 重复的表达
- 闲聊和无意义内容
- 详细的代码/日志（只保留要点）
- 过时的上下文

### 输出格式

压缩后生成结构化摘要：

```markdown
## 对话摘要

### 核心主题
[一句话概括]

### 用户偏好
- [偏好1]
- [偏好2]

### 待办事项
- [ ] 待办1
- [ ] 待办2

### 重要结论
- 结论1
- 结论2

### 关键信息
- 信息1
- 信息2

### 最近对话（保留）
[最近3-5轮对话保留完整]
```

### 使用方式

当需要压缩时，执行以下步骤：

1. 读取当前对话历史
2. 检查熔断器状态（compaction_state.json）
3. 若 circuitOpen，通知用户并跳过
4. 分析并提炼核心信息
5. 生成结构化摘要
6. 用摘要替换原始对话历史
7. 成功则重置熔断器，失败则累加 consecutiveFailures
