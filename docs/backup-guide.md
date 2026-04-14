# OpenClaw 备份指南

## 备份策略

### 需要备份的关键文件

```
/Users/mac/.openclaw/
├── openclaw.json          # 主配置文件
├── workspace/
│   ├── SOUL.md            # 自我定义
│   ├── USER.md            # 用户信息
│   ├── AGENTS.md          # 代理配置
│   ├── MEMORY.md          # 长期记忆
│   └── memory/            # 日常记忆
└── agents/                # agent会话状态
```

### 备份方式

1. **本地备份**：复制到指定备份目录
2. **远程备份**：可使用 iCloud、Dropbox 等云存储

### 恢复方式

1. 从备份目录复制文件回原位置
2. 重启 OpenClaw gateway

## 自动备份 (TODO)

建议设置 cron 任务实现每日自动备份：
- 触发条件：距离上一次备份超过24小时
- 备份方式：本地 + 远程

---

## 模型池配置 (2026-03-22)

### 高速池
- step-2-mini (主)
- step-1-8k, MiniMax-M2.5-Lightning (备)

### 智能池
- step-1-256k (主)
- step-3, MiniMax-M2.5 (备)

### 文本池
- step-1-32k (主)
- step-3.5-flash (备)

技能：`model-pool-selector` 已安装
