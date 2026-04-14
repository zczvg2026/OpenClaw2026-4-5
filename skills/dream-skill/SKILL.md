---
name: dream-skill
version: 1.0.0
description: "Agent dreaming — autonomous memory consolidation. Inspired by Claude Code's auto-dream mechanism. Part of the DaZhaXie memory architecture."
author: dazhaxie
---

# Dream Skill 🦀💤

每24小时由 cron 自动触发，在后台整理记忆。

## 触发条件

- cron 驱动：`--every 24h`，凌晨02:00 (Asia/Shanghai)
- session 类型：`isolated`（独立子agent，不污染主会话）
- 无需 deliver，不主动通知用户

## 做梦流程

### 1. 检查锁

读取 `memory/.dream-lock.json`，检查 `dreaming: true` 是否存在。
如果已在做梦（异常中断），直接退出。

### 2. 获取锁

写入 `memory/.dream-lock.json`：
```json
{
  "dreaming": true,
  "startedAt": "<ISO时间>",
  "sessionsReviewed": 0
}
```

### 3. 扫描新会话

读取 `memory/` 目录下的每日笔记，按修改时间排序。
识别自上次做梦以来有新变化的笔记文件。

### 4. 执行4阶段整合

详见 `CONSOLIDATION_PROMPT.md`

### 5. 释放锁

完成后更新 `memory/.dream-lock.json`：
```json
{
  "dreaming": false,
  "lastDreamedAt": "<ISO时间>"
}
```

## 记忆文件结构

```
workspace/
├── MEMORY.md                # 入口索引（纯指针，每条目≤150字符，≤10KB）
└── memory/
    ├── .dream-lock.json     # 锁文件
    ├── YYYY-MM-DD.md        # 每日原始笔记（追加，不修改）
    ├── user-johnson.md      # 用户档案
    ├── tools-config.md      # 工具配置
    ├── key-lessons.md       # 关键经验教训
    ├── projects.md          # 项目状态
    └── company-info.md      # 公司信息
```

**MEMORY.md 是索引，memory/*.md 是内容。禁止把内容写进 MEMORY.md。**
```

## 注意事项

- Bash 只允许只读命令（ls/cat/find/grep/stat）
- 写操作只针对 memory/ 目录下的 .md 文件
- 整合时删除矛盾、过时的记忆
- 绝对日期替代相对日期（"昨天"→"2026-04-01"）
