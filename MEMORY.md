# MEMORY.md — 长期记忆入口

> 索引；详细内容在对应 topic 文件。

## 用户
- [Johnson 档案](memory/user-johnson.md) — 太擎创始人，出差北上杭蓉，直击本质；"先XXX"=只做XXX；流水线分工确认（Johnson拍+审，我全执行）

## 工具配置
- [工具配置](memory/tools.md) — mcporter生图/Meigen/LibTV/飞书全套/Obsidian（本地vault，读写无需Key）；API Key存.zshrc

## 方法论
- [产品思考三步法](memory/knowledge/three-step-thinking.md) — 苏格拉底提问→第一性原理→奥卡姆剃刀；必须固化进所有产品/方向讨论（Johnson 2026-04-05确认）
- [六步审问法](memory/knowledge/six-step-interrogation.md) — AI读行业报告框架

## 日记标准（2026-04-12 确认）
- 格式：frontmatter + 二级标题分段 + **加粗** + `-` Bullet + `>` 金句
- 每日22:30 cron触发 → 飞书预览 → Obsidian写入
- 模板见 HEARTBEAT.md「日记格式标准」章节

## 用户偏好（2026-04-05 新增）
- **协议 > 应用**：AI agent大爆发后，垂直领域协议比通用协议更现实；财税智能体5月上市可考虑"协议思维"设计产品API
- **每天早上 Dream 汇报**：Dream cron完成后主动向Johnson推送结果
- **并行任务**："都做"→ 直接并行spawn，不串行
- **视频号风格**：口播默认轻松口语，少用"我是xxx创始人"，多用真实感受
- **飞书文档分享即开公网权限**：创建后主动开启"互联网上获得链接的人可阅读"
- **IMA知识库主动读**：Johnson上传了所有公司资料，要求我主动读取加深理解（19篇笔记已读）

## 关键教训
- [key-lessons.md](memory/key-lessons.md) — 完整经验教训库（2026-04-05整理去重）
- 陌生内容任务第一步查skills/，不先用curl/web_fetch/summarize
- IMA日记标准流程：飞书预览→Johnson确认→IMA写入（`import_doc`格式不稳定）
- isolated cron不能主动推飞书，必须main session + systemEvent
- 工具配置立即入库TOOLS.md，不要等
- LibTV视频素材用公网CDN URL文本发送，不用本地路径

## 项目状态（2026-04-05 更新）
- [太擎/域擎/ENERGY CELL](memory/projects.md) — 三条完全独立方向同时跑：
  - 太擎（汉数旗下品牌）：财税智能体，代理+对赌收购路径
  - 域擎（新注册）：OPC联盟平台，自建路径
  - ENERGY CELL（2026-04-02商业计划书）：健康品牌S2B2C，与太擎/域擎完全独立，无关联
- [视频号日更](memory/projects.md) — E01-E07脚本✅，E01-E05素材✅，口播文案等Johnson补充个人信息
- [AI嘉年华](memory/projects.md) — ✅确认推进，广州+成都，规模/时间待定
- [Da Zha Xie能力](memory/projects.md) — 飞书✅/心跳✅/做梦✅/提取✅/IMA✅

## 公司信息
- [太擎/探迹架构](memory/company-info.md) — 探迹科技（母，全球独角兽）→ 汉数/探域/探迹国际 → 太擎（代理，对赌并入）；域擎（新品牌，自建）
