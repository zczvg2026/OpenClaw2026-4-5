# MEMORY.md — 长期记忆入口

> 索引；详细内容在对应 topic 文件。
> 最后更新：2026-04-27

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

## 用户偏好
- **协议 > 应用**：AI agent大爆发后，垂直领域协议比通用协议更现实
- **每天早上 Dream 汇报**：Dream cron完成后主动向Johnson推送结果
- **并行任务**："都做"→ 直接并行spawn，不串行
- **视频号风格**：口播默认轻松口语，少用"我是xxx创始人"，多用真实感受
- **飞书文档分享即开公网权限**：创建后主动开启"互联网上获得链接的人可阅读"
- **IMA知识库主动读**：Johnson上传了所有公司资料，要求我主动读取加深理解

## 关键教训
- [key-lessons.md](memory/key-lessons.md) — 完整经验教训库
- 陌生内容任务第一步查skills/，不先用curl/web_fetch/summarize
- IMA日记标准流程：飞书预览→Johnson确认→IMA写入（`import_doc`格式不稳定）
- isolated cron不能主动推飞书，必须main session + systemEvent
- 工具配置立即入库TOOLS.md，不要等
- LibTV视频素材用公网CDN URL文本发送，不用本地路径

## 项目状态（2026-04-27 更新）
- [太擎/域擎](memory/projects.md) — 探迹体系内并列方向：
  - 太擎（探迹技术品牌）：企业级智能体PaaS，Johnson是代理商+对赌收购路径
  - 域擎（探迹商业品牌）：数智员工平台，核心壁垒是双向飞轮生态
  - ENERGY CELL（已终止，未实际运营）
- [视频号日更](memory/projects.md) — E01-E07脚本✅，E01-E05素材✅，口播文案待Johnson补充个人信息
- [AI嘉年华](memory/projects.md) — ✅确认推进，广州+成都，规模/时间待定
- [Da Zha Xie能力](memory/projects.md) — 飞书✅/心跳✅/做梦✅/提取✅/IMA✅

## 公司信息
### 探迹体系结构（2026-05-08 重大修正）
- **探迹（母）**：全球AI独角兽，估值13亿美元，阿里/红杉/凯辉/软银投资
- 旗下**六板块**并列：探迹(母) / 太擎(PaaS) / 旷湖(数据) / **域擎(解决方案)** / **探域(客服智能体)** / 探迹国际(跨境)
- **域擎 ≠ 探域**：两者是探迹体系内**不同子公司**，域擎=解决方案平台，探域=客服智能体平台
- **太擎 = 企业级智能体开发PaaS平台**（技术品牌）
- **域擎 = 数智员工赋能平台**，核心壁垒是**双向飞轮生态**
- 详细架构：[memory/company-info.md](memory/company-info.md)（2026-05-08 全面重写）

### 关键产品
- 滴灌营销：轻享¥9,600 / 精英¥16,980 / 尊享¥98,000 / 旗舰¥298,000
- OPC入门包¥8,980 = 一人公司打造费用
- 财税智能体：6月30日上线（5.1推迟）

### 关键定义
- **OPC = One Person Company（一人公司）**
- **双向飞轮** = 域擎核心壁垒：招商企业↑→创业者机会↑→企业增长↑→循环

## 系统状态（2026-04-27 更新）
- **Gateway**：4.9版本，PID 39111，正常运行
- **日记Cron**：33042b94，修复 delivery target ✅，今晚22:30验证
- **清理**：memory.bak ✅ / 旧IMA skills ✅ / 草稿文件 ✅
