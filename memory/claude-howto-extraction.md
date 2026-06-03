# Claude How To × OpenClaw 萃取报告

> 来源：luongnv89/claude-howto（12.9k stars，MIT）
> 分析日期：2026-04-29
> 目的：汲取通用设计理念，映射到 OpenClaw 能力体系

---

## 一、Subagents 模式 — 对我最有启发

Claude Code 的 subagent 定义格式（`.md` 文件，YAML frontmatter）：

```yaml
---
name: code-reviewer
description: Expert code review specialist. Use PROACTIVELY after writing or modifying code.
tools: Read, Grep, Glob, Bash
model: inherit
---

# Code Reviewer Agent
You are a senior code reviewer ensuring high standards...
## Review Priorities (in order)
1. Security Issues
2. Performance Problems
3. Code Quality
...
## Review Checklist
- Code is clear and readable
- Functions are well-named
...
## Review Output Format
For each issue:
- **Severity**: Critical / High / Medium / Low
- **Location**: File path and line number
- **Suggested Fix**: Code example
```

**对 OpenClaw 的启发：**

我们现有的 subagent 是通过 `sessions_spawn` + `task` 字符串直接内联的，没有独立定义文件。

**可演进方向：**
```
~/.openclaw/workspace/agents/
  code-reviewer.md    # 专业化 agent 定义
  test-engineer.md
  documentation-writer.md
```

每个 agent 独立文件，包含：
- YAML frontmatter（元数据）
- 详细 system prompt（角色定义 + 优先级 + 输出格式）
- 调用方式文档

**好处：**
1. agent 定义可版本控制、可共享
2. prompt 不混在代码里，易维护
3. 可批量注册到 agent pool，按需调用

---

## 二、Hooks 模式 — 事件驱动的自动化

Claude Code 有 5 类 hook 共 28 个事件。关键示例：

### SessionEnd Hook（session-end.sh）
**功能：** session 结束时主动询问"今天学了什么模块"，记录到 `~/.claude-howto-progress.json`

```bash
# 核心逻辑
echo " Which modules did you work on?"
read INPUT
python3 - "$PROGRESS_FILE" "$DATE" "$TIME" "$MODULES_JSON" "$NOTES" <<'PYEOF'
# 追加到 JSON 文件
data.setdefault('sessions', []).append(new_session)
PYEOF
```

**对 OpenClaw 的启发：**

OpenClaw 目前没有等效的 SessionEnd hook。但我们可以用 cron 近似实现：
- 每天结束时（22:30 cron）记录当天工作的模块
- 问题是 cron 是时间驱动，不是事件驱动

**更接近的等价方案：**
- HEARTBEAT.md 里记录每天的工作模块标签
- 日记里包含 "今日主要工作模块" 字段
- 比 Claude Code 的交互式询问弱，但符合我们的工具现状

---

### Context Tracker Hook（context-tracker.py）
**功能：** 每次对话前后计算 token 使用量，输出到 stderr

```python
# 核心逻辑
def handle_user_prompt_submit(data):
    transcript_content = read_transcript(transcript_path)
    current_tokens = count_tokens_estimate(transcript_content)
    save_to_temp_file(session_id, current_tokens)

def handle_stop(data):
    delta = current_tokens - pre_tokens
    print(f"Context: ~{current_tokens:,} tokens ({percentage:.1f}% used)")
```

**对 OpenClaw 的启发：**

OpenClaw 的 `session_status` 已经显示 token 和 context 百分比。但：
- 没有"每次消息后自动报告变化量"的机制
- 没有 temp file 做跨消息状态跟踪

**可行改进：**
在 AGENTS.md 或 HEARTBEAT.md 里加一个 context 管理意识规则，当 context > 80% 时主动提示压缩。

---

### Pre-Tool-Check Hook（pre-tool-check.sh）
**功能：** 工具执行前验证（如 exec 前检查危险命令）

```bash
# 检查是否包含危险操作
if echo "$COMMAND" | grep -E "(rm -rf|sudo|chmod 777)"; then
  echo "⚠️  Warning: dangerous command detected"
fi
```

**对 OpenClaw 的启发：**

我们已有 `security: "deny"` 等 exec 安全模式。这个 hook 提供了更细粒度的运行时检查思路。

---

## 三、Skills 模式 — 能力封装

Claude Code skill 结构：
```
03-skills/
  code-review/
    SKILL.md         # 主定义
    scripts/         # 辅助脚本
    templates/       # 输出模板
```

**对比 OpenClaw skill：**
```
~/.openclaw/skills/
  github/
    SKILL.md        # 主定义
  notion/
    SKILL.md
```

**差距：** Claude Code 的 skill 有 `scripts/` 和 `templates/` 子目录，我们 skill 普遍是单文件 SKILL.md。

**可演进方向：**
给复杂的 skill（如 wechat-article-parser、ima-skill-new）加上 scripts/ 和 templates/，把提示词和脚本拆开，更易维护。

---

## 四、最值得借鉴的组合模式

Claude How To 给的"真正的高手是组合使用"案例：

### Automated Code Review
```
Slash Command `/review-pr`
  → 加载 project memory（编码规范）
  → GitHub MCP 获取 PR 内容
  → 委托 code-reviewer subagent（安全审查）
  → 委托 test-engineer subagent（测试覆盖）
  → 综合输出
```

**对 OpenClaw 的启发：**

我们没有 GitHub MCP，但可以设计类似的飞书审查流：
```
每天 cron 22:30 日记生成
  → 加载 HEARTBEAT.md（今日任务清单）
  → 加载 MEMORY.md（长期上下文）
  → 加载 memory/YYYY-MM-DD.md（当日日志）
  → 生成日记摘要
  → 发飞书给 Johnson
  → 等确认后写入 IMA 知识库
```

这就是一个"飞书日记流水线"，已经是组合使用。

---

## 五、总结：可落地的 3 件事

| 优先级 | 行动 | 收益 |
|--------|------|------|
| P1 | 给 cron subagent 加上结构化的 system prompt（类似 code-reviewer.md 的格式），明确任务步骤和输出格式 | cron 执行更稳定，减少随机发挥 |
| P2 | 在 AGENTS.md 加 context 管理意识规则（>80% 提示压缩） | 减少 context 耗尽导致的执行失败 |
| P3 | 建立 `~/.openclaw/workspace/agents/` 目录，把常用的 subagent prompt 独立成文件 | agent 定义可复用、可版本控制 |

---

## 六、不适用的部分

以下 Claude Code 特性没有 OpenClaw 等价物，不需要研究：
- Slash Commands（Claude Code 特有 CLI 交互方式）
- `/plugin install`（插件系统不兼容）
- CLAUDE.md 多层级 memory（我们用 MEMORY.md + HEARTBEAT.md 替代）
- MCP servers（Model Context Protocol，OpenClaw 架构不同）
- Checkpoints/rewind（session 快照，OpenClaw 是文件持久化）
- Extended Thinking toggle（Claude Code 特有，OpenClaw 用不同模型替代）
