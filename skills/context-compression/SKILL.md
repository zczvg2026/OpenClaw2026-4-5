# Context Compression Skill

当对话上下文接近 token 上限时，自动将对话历史压缩为摘要，保留关键信息。

## 自动触发阈值

- **警告阈值**：剩余 `< 20_000` tokens → 发飞书警告给用户
- **压缩阈值**：`effectiveContextWindow - 13_000` tokens 剩余时触发
- **强制压缩**：剩余 `< 5_000` tokens → 立即压缩，不等确认

> 例如：effectiveContextWindow = 200_000，则压缩阈值 = 187_000（剩余），即已用 13_000 tokens 时触发。

## 熔断器（Circuit Breaker）

状态存 `memory/compaction_state.json`：

```json
{
  "consecutiveFailures": 0,
  "lastFailureAt": null,
  "circuitOpen": false
}
```

**规则：**
- 每次 compaction 失败：`consecutiveFailures++`
- 成功：重置为 0
- `consecutiveFailures >= 3`：停止自动压缩，`circuitOpen: true`
- 通知用户："context 压缩连续失败3次，已暂停自动压缩，请手动处理或重启 session"
- 熔断打开后需人工介入（删除 `compaction_state.json` 或手动重置 `circuitOpen: false`）才恢复

## 压缩原则

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

## 输出格式

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

## 使用方式

当需要压缩时，执行以下步骤：

1. 读取当前对话历史
2. 检查熔断器状态（读取 `memory/compaction_state.json`）
3. 若 `circuitOpen: true`，通知用户并跳过
4. 分析并提炼核心信息
5. 生成结构化摘要
6. 用摘要替换原始对话历史
7. 成功：重置熔断器（`consecutiveFailures = 0`）
8. 失败：累加 `consecutiveFailures`，若 >= 3 则打开熔断器

## 手动触发

- 用户明确要求"压缩上下文"、"总结对话"、"精简一下"
- 对话轮次超过 20 轮
