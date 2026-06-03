# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

## 每日Eval自检

每日起床后（第一次心跳），对照6条Eval自检昨天的工作：

| # | 检查项 | 昨日得分 |
|---|--------|----------|
| 1 | 交付前停顿，逐条过 Eval？ | — |
| 2 | 先搜索记忆？ | ✅ |
| 3 | 结论先行？ | ✅ |
| 4 | 在能力范围内？ | ✅ |
| 5 | 不确定时说"不确定"？ | ✅ |
| 6 | 简洁？ | ✅ |
| 7 | 幽默？ | ✅ |

**新增必检项（2026-03-31）：**
| 7 | 读图/读文件成功才分析？ | ✅ |
| 8 | 路径/特殊字符优先用 write？ | ✅ |
| 9 | 交付前停顿已养成习惯？ | — |

做得好保持，做得不好记录到 .learnings/LEARNINGS.md 并反思改进。

## 每日日记（Obsidian 优先，2026-04-03 起）

每天 **22:30** 自动触发（cron job: JOB-13B6），分三步：

**Cron 自动执行：**
1. 生成当日日记摘要
2. 发飞书给 Johnson 预览

**等待确认后（手动）：**
3. 收到确认后，写入 Obsidian（`日记/YYYY-MM-DD.md`）
4. 同时推飞书文档一篇

**日记存储路径：** `/Users/mac/Documents/Obsidian Vault/0-raw/大闸蟹日记/YYYY-MM-DD.md`

**格式标准：** 见下方「日记格式标准」章节（2026-04-12 确认）

---

## 日记格式标准（2026-04-12 确认）

每篇日记必须包含以下结构：

```markdown
---
date: YYYY-MM-DD
tags: [日记, 每日]
---

# 大闸蟹每日日记 - YYYY-MM-DD

## 今日最重要的一件事
（一句话概括今日核心成果）

## 主要工作内容
- **加粗小标题**：内容详细说明
- Bullet 列表分条描述

## 今日教训
- 今日犯的错误或踩的坑

## 明日展望
- 明天要做什么

## 今日金句
> 引言（如果当日有的话）
```

**格式要求：**
- frontmatter 必须包含 date + tags
- 二级标题 `##` 分段
- 关键词/标题加粗 `**`
- 列表用 `-` Bullet
- 金句用 `>` 引言块
- 写完后推 Obsidian `大闸蟹日记/` 文件夹

---

## 失败轨迹自动蒸馏（2026-05-01 确认）

每 **3 次心跳**（约 1.5 小时），自动运行一次 distill 扫描：

```bash
python3 ~/.openclaw/workspace/.learnings/distill.py --scan
```

**执行规则：**
- 发现失败轨迹 → 写入 `.learnings/distill/` → 在心跳回复末尾加一句"已自动记录 X 条教训"
- 未发现 → 不说话（静默）
- 每次扫描后重置计数

**计数追踪：** `memory/heartbeat-state.json` 的 `heartbeatCount` 字段

---

## 执行流程（Cron 触发）

cron fires at 22:30 → spawn subagent → 生成日记 → 发飞书给Johnson → 等确认 → 推 Obsidian + 飞书文档

- compaction 已配置 safeguard + memoryFlush，会自动触发
- 仅当 session 对话轮次明显过长（>20轮）时，主动提议压缩
- **不要**每次心跳都读 memory/ 文件查日期，避免 token 浪费
