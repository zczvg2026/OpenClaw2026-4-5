# Checkpoint System

> Qclaw qmemory 启发：WAL 检查点崩溃恢复。

## 用途

多步骤任务执行时，在每一步写 checkpoint，会话中断后能续上。

## 文件位置

`/Users/mac/.openclaw/workspace/checkpoints/<task-label>.json`

## 格式

```json
{
  "task": "任务描述",
  "label": "唯一标签",
  "startedAt": "ISO 时间戳",
  "updatedAt": "ISO 时间戳",
  "status": "running|done|failed",
  "steps": [
    {
      "step": 1,
      "name": "步骤名",
      "status": "done",
      "detail": "结果摘要",
      "timestamp": "ISO 时间戳"
    }
  ],
  "context": {
    "filesCreated": ["path1", "path2"],
    "errors": ["err1"]
  }
}
```

## 命令速查

- 开始任务：`write checkpoints/<label>.json`（status=running）
- 记录步骤：`edit` 追加 steps[]
- 完成/失败：`edit` 改 status
- 续上：`read checkpoints/<label>.json` → 看 steps 跳过已完成的
