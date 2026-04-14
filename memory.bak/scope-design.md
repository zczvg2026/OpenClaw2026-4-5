# 双层记忆作用域设计

> 参考：Claude Code private vs team 双层架构
> 设计者：大闸蟹 🦀
> 日期：2026-04-04

---

## 一、为什么要分层

当前记忆系统只有单一作用域，private 和 team 混合在一起。

**问题场景**：
- 我在群聊中可能无意引用了 Johnson 的私人反馈（比如"他不喜欢我跳步"）→ 泄露私人背景
- 新来一个协作者，想接入记忆系统 → 所有记忆一股脑给出去，private 内容暴露

**解决方案**：双层作用域
- **private**：仅 AI 可见，用于直接 1:1 对话上下文
- **team**：多用户/协作场景下可共享

---

## 二、两个作用域的定义

### private — 私人记忆

**特征**：关于 Johnson 本人的一切，包括：
- 私人偏好（沟通风格、幽默感、直觉判断）
- 私人背景（出差习惯、健康、情绪状态）
- 对我的私人反馈（纠正、确认、偏好）
- 工具配置（API key、CLI 路径）
- 私人项目（不涉及公司/团队的工作）

**判断标准**：如果这份记忆分享给陌生协作者，Johnson 会感到不自在吗？
- 会 → private

### team — 团队记忆

**特征**：Johnson 愿意开放给团队/协作者的信息，包括：
- 公司基本信息（太擎/域擎定位、战略阶段）
- 团队规范（域擎六条原则）
- 共享项目状态（视频号进度、Claude Code 研究结论）
- 团队成员公开信息（名片上的事实）
- 外部知识引用（六步审问法、商业分析框架）

**判断标准**：如果这份记忆分享给团队新成员，会帮助他快速上手吗？
- 会 → team

---

## 三、标记格式

每个记忆文件头部 YAML frontmatter 加入 `scope` 字段：

```yaml
---
scope: team
---
```

**判断优先级**（冲突时）：
1. 明确私密 → private（不冒险）
2. 明确团队共享 → team
3. 模糊地带 → private（保守原则）

---

## 四、文件分类清单

| 文件 | scope | 判断理由 |
|------|-------|----------|
| memory/2026-03-20.md | private | 大量私人会话记录、Eval 自检 |
| memory/2026-03-22.md | private | 私人会话反馈、钱Baibai框架使用记录 |
| memory/2026-03-25.md | private | 私人工作日志、渐进式迭代教训 |
| memory/2026-03-26.md | private | 私人 Eval 自检 |
| memory/2026-03-27.md | private | 私人 Eval 自检 |
| memory/2026-03-29.md | private | 私人会话记录、大闸蟹 vs Q小倩冲突分析 |
| memory/2026-03-30.md | private | 私人会话、Kuaifa 配置 |
| memory/2026-04-01.md | private | 私人会话（Claude Code 源码路径） |
| memory/2026-04-02.md | private | 私人会话、记忆系统设计私人笔记 |
| memory/2026-04-03.md | private | 私人会话（跳步反馈、视频号私人观察） |
| memory/company-info.md | team | 太擎/域擎公司公开信息 |
| memory/course-principles.md | team | 域擎六条原则，团队规范 |
| memory/key-lessons.md | private | 私人教训（cron session 错误、IMA 配置路径） |
| memory/projects.md | team | 项目状态，可供团队参考 |
| memory/user-johnson.md | private | Johnson 私人偏好、沟通习惯 |
| memory/tools.md | private | API token、CLI 配置路径 |
| memory/taxonomy.md | team | 记忆系统设计原则（通用方法论） |
| memory/video-series.md | team | 视频号内容定位（对外公开） |
| memory/video-scripts/WEEK1-UNIFIED.md | private | 含私人拍摄风格反馈 |
| memory/video-scripts/VIDEO-WORKFLOW.md | team | 流水线分工文档，可共享 |
| memory/video-scripts/2026-04-03.md | private | 私人会话日志 |
| memory/video-scripts/2026-04-04.md | private | 私人会话日志 |
| memory/video-scripts/2026-04-05.md | private | 私人会话日志 |
| memory/knowledge/six-step-interrogation.md | team | 外部知识方法论 |
| memory/knowledge/awesome-openclaw-skills.md | team | 外部知识 |
| memory/knowledge/meigen.md | private | API token 配置 |

---

## 五、使用规则

### 加载规则

**主会话（飞书 direct 1:1）**：
- 加载所有 private + team 文件

**群聊（多人场景）**：
- 只加载 team 文件
- 不引用任何 private 内容

**isolated cron session**：
- 只加载 team 文件
- private 信息通过 main session 推送，不直接访问

### 写入规则

**私人反馈写入**：
- Johnson 的私人纠正 → `memory/key-lessons.md`（private）
- Johnson 的私人偏好 → `memory/user-johnson.md`（private）
- 每日会话日志 → `memory/YYYY-MM-DD.md`（private）

**团队信息写入**：
- 项目进展 → `memory/projects.md`（team）
- 公司信息 → `memory/company-info.md`（team）
- 团队规范 → `memory/course-principles.md`（team）

### 边界情况

Q：某个 daily log 里混合了 private 和 team 内容怎么办？
A：整个文件标记为 private（保守原则），team 内容在 team 文件中独立维护。

Q：新成员加入时，如何给记忆？
A：先给 team 文件，让他了解上下文；private 文件按需给。

Q：私人文件里是否可以放 team 内容？
A：可以，但不推荐——private 文件在群聊中不加载，内容可能无法被团队利用。

---

## 六、实施清单

- [x] scope-design.md（本文）
- [x] 所有 daily logs 加 scope frontmatter
- [x] 所有独立 md 文件加 scope frontmatter
- [x] 更新 AGENTS.md 中相关加载规则
