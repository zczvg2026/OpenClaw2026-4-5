# Audit Log

> Qclaw 审计日志启发：每条用户消息 + 关键操作记录，有据可查。

## 日志文件

`.audit/log.jsonl` — 每行一个 JSON 对象，追加写入。

## 记录格式

```json
{"ts": "ISO8601", "type": "message|checkpoint|error|decision", "channel": "feishu|direct", "summary": "一句话摘要", "tokens": 1234}
```

## 记录规则

| 类型 | 触发条件 |
|------|---------|
| `message` | 每条用户消息 |
| `checkpoint` | 新建/更新 checkpoint |
| `error` | 任务失败/异常 |
| `decision` | 重要决策（如架构选择、配置变更） |
