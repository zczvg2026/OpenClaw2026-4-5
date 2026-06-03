---
name: self-improvement
description: "从 Qclaw 架构中汲取的能力提升：任务检查点、游标记忆、中间件式 prompt 编排"
metadata:
  openclaw:
    emoji: "🦀"
---

# 大闸蟹自进化

> 学 Qclaw 架构，做的 3 件事：

## 1. Checkpoint 系统（← qmemory）

多步骤任务写 checkpoint，中断后能续。

**详见**：`docs/checkpoint-system.md`

## 2. 游标防重复提取（← auto-memory）

日记先行，定时提纯，游标记录上次处理位置。

**详见**：`.auto-memory/CURSOR.md`

## 3. Prompt 段落化（← prompt-optimizer）

所有指令按 `## 标题` 段落组织，方便注入/重排/覆盖。

已在以下文件应用：
- SOUL.md — 按 ## 分节
- AGENTS.md — 按 ## 分节
- HEARTBEAT.md — 按 ## 分节
