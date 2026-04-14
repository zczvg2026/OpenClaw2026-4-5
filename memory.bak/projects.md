---
scope: team
---

# 项目状态

## 太擎 / 域擎（2026-04）
**阶段**：第二阶段 — 应用生产
**进展**：OpenClaw 底座已搭，下一步搭到能演示
**负责人**：Johnson

## ENERGY CELL 活力基因 S2B2C（2026-04-02 新发现，2026-04-05 确认独立项目）
**内容**：健康品牌商业计划书，悠悠富氢水机做高频流量入口 + 健康产品高利变现
**核心逻辑**：水机建立社区信任 → 产品高利转化
**资料位置**：IMA知识库 doc_id: 7445467122112462
**关键更新**：2026-04-05 Johnson确认ENERGY CELL与域擎OPC联盟是**两个完全独立的项目**，没有关联
**状态**：独立推进，与太擎/域擎平行

## IMA 知识库深度读取（2026-04-05 ✅ 完成）
**规模**：19篇笔记（ClientID: 1d7058d8e7695e4fb7127a168057977e）
**关键发现**：
- 混沌创商院课程（讲师：钱琼炜）：战略/创新方法论（单点战略/贝叶斯/右上角理论/破局创新）
- ENERGY CELL S2B2C 商业计划书（2026-04-02，新鲜）：健康品牌，富氢水机做高频入口
- 企业战略研讨 + AI时代战略思辨
- OpenClaw热潮：SaaS → Agentic as a Service，一人公司模式崛起
- 律师团队AI营销战略
- **重大认知更新**：
  - Johnson 上混沌创商院是带着问题实战打磨，不是学知识
  - ENERGY CELL 与 域擎 OPC联盟 是**两个完全独立项目**，无关联
  - 太擎线（代理，对赌收购）vs 域擎线（自建，新品牌）同时平行跑
  - 资料位置：所有公司资料在IMA知识库（要求我主动读取加深理解）

## Claude Code 泄露事件（2026-04-01）
**源码位置**：~/Desktop/zczvg/claude-code-complete/（1423个.ts文件）
**改写版**：claw-code（instructkr），只有骨架，不可执行
**最有价值模块**：权限分类引擎（⭐⭐⭐⭐⭐）
**建议**：研究其设计思路作为大客户"安全故事"，不自建不自采
**详细记录**：memory/2026-04-01.md

## LibTV AI Video 集成（2026-04-02）
- **Key格式**：`sk-libtv-xxxxxxxx`（OpenAI格式）
- **正确Key**：`sk-libtv-09eabe09c16e4cc08126bad086b23f62`
- **Base URL**：`https://im.liblib.tv/openai/session`
- **状态**：API全通（对话/Agent/图片生成均✅），视频模型全要VIP会员❌
- **可灵O1等模型**：可绕过VIP限制，直接调原厂API（待集成）
- **配置**：Key存于 `~/.openclaw/workspace/skills/libtv-skill/.env`

## AI 嘉年华（2026-04-02 启动，✅确认推进）
**目标**：在广州、成都各办一场 AI 线下活动，扩大太擎影响力
**地点**：广州、成都（待确认具体城市）
**状态**：✅ 确认推进（2026-04-02 下午 Johnson 确认）
**待确认**：目标（品牌/招募/转化）、规模、时间、预算、场地
**负责人**：Johnson

## GitHub 备份仓库（2026-04-04 21:05 ✅ 已推送）
- **仓库**：git@github.com:zczvg2026/OpenClaw.git
- **内容**：1052 个文件（workspace 全量备份）
- **SSH Key**：`~/.ssh/id_ed25519.pub`（Johnson 已添加到 GitHub 账户）
- **首次推送**：21:05 CST 完成（首次push需拉取远程README后rebase再push）
- **自动备份**：每天 21:00 CST 执行 `~/.openclaw/auto-backup.sh` → commit + push
- **备份脚本**：`~/.openclaw/auto-backup.sh`（解决 crontab 里 $(date) 预计算问题）
- **日志**：`~/.openclaw/logs/backup.log`

## 龙虾 SOP + 能力表（2026-04-04 20:34 ✅）
- **SOP文档**（飞书文档）：https://feishu.cn/docx/MJ6hdhTbMo0ooex8BhfcdcRrnBg
  - 含：初始化清单 / 日常养护 / Skill安装四步 / 异常处理 / 评分维度 / 8条红线 / 命令速查
  - 已开启「互联网上获得链接的人可阅读」✅
- **龙虾能力表**（bitable）：https://wcn1vdjagxl2.feishu.cn/base/AnNYbZEExamjupspFxScYTWhnne
  - 已录入 10 个核心技能，含质量/速度/稳定性三维评分
  - 已开启「互联网上获得链接的人可阅读」✅
- **背景**：Johnson 晚间验收 Q3 龙虾能力表时要求两份文件都开启公网阅读

## 过期Cron任务清理（2026-04-05 ✅ 已禁用）
**任务名**：安装 ClawHub 技能（cron id: `4541798a-a103-40c2-b4cb-4403380eb31a`）
**问题**：每6小时执行一次clawhub install，向飞书推送安装状态结果，造成每日重复噪音
**发现**：Johnson 反映飞书每天早上收到技能安装列表 → 追查发现该cron持续推送
**状态**：✅ **已禁用**（2026-04-05 22:07 CST）
**执行**：Gateway 重启后 `openclaw cron disable 4541798a-a103-40c2-b4cb-4403380eb31a` 成功
**教训**：cron任务完成后应立即禁用或删除，不能"留着以后可能用"；Gateway 故障时 cron disable 会静默失败，需验证 jobs.json 里 `"enabled": false`

## Da Zha Xie — 能力建设
- ✅ 飞书集成（会话、日历、知识库）
- ✅ 定时 cron（起床/喝水/睡觉提醒，自动技能更新）
- ✅ 每日心跳检查
- ✅ 做梦机制（2026-04-02 落地，每24小时深度整合）
- ✅ 提取机制（2026-04-02 落地，每30分钟增量捕获）
- ✅ 通用记忆体系 v1（taxonomy：user/feedback/project/reference）
- ✅ P0 权限分级确认机制（2026-04-04，memory/agent-tool-permissions.md）
- ✅ P1 private/team 双层记忆作用域（2026-04-04，memory/scope-design.md）

## Claude Code + WeChat文章对比分析（2026-04-04）
- Johnson 重读 Claude Code 源码（~/Desktop/zczvg/claude-code-complete/）+ WeChat文章
- 核心结论：Harness层面优化 > 追求更强模型
- 产出：P0+P1 优化任务并行完成
- ✅ IMA 日记写入打通（2026-04-03 深夜）
  - ⚠️ 2026-04-04 更新：Johnson 确认要**每天新建一篇笔记**（用 `import_doc`），不要追加到同一篇
  - ⚠️ 2026-04-05 更新：IMA `import_doc` 渲染不稳定，标准流程改为**飞书预览 → 用户确认 → IMA 写入**
  - 最新日记 note_id（2026-04-04）：`7446225750071610`（先飞书预览后写入，格式确认 ✅）
  - 每篇 note_id 记录在 `memory/YYYY-MM-DD.md` 的 `ima_note_id` 字段
  - 写日记脚本：`~/.openclaw/workspace/skills/ima-note/scripts/write_diary.py`
- ✅ OpenCLI Chrome 扩展（2026-04-03 深夜，待 Johnson 加载确认）
- ✅ 权限分级方案 v1（2026-04-04，memory/agent-tool-permissions.md）— 三级权限：read-only/write/destructive，subagent 完成，Johnson 确认
- ✅ 双层记忆作用域（private/team，2026-04-04，memory/scope-design.md）— subagent 完成，17 private + 10 team 文件，Johnson 确认
- ✅ Claude Code 源码 + WeChat文章对比分析（2026-04-04）— 核心结论：Harness工程是AI能力差距的根本，Johnson 确认
- ✅ 视频号起号攻略研究（2026-04-04 凌晨 ✅）— 最佳发布时间：12-13点/18-21点；前3秒钩子最关键；日更最佳；已整合进流水线
- ✅ Claude Code源码+WeChat文章对比分析（2026-04-04 08:00 ✅）— 核心结论：Harness工程是差距根本；5个优化优先级已确认（P0权限分级+P1双层作用域已落地）
- ⚠️ Extract transcript 读取精度待优化（JSONL 格式匹配漏洞）
- ⚠️ 飞书会话历史读取限制：cron 子 session 无法直接读 direct session history，需 main session 主动推送
- ⚠️ OpenClaw Chrome 扩展（opencli）：需用户在 Chrome 图形界面手动加载，技术上无法自动化安装

## 视频号日更计划

### 最新状态（2026-04-04 09:43 更新）
**拍摄方案**：混合模式 — Johnson 只拍一次（2-3分钟自我介绍），拆成多段复用，多期不用重拍
**脚本风格**：更轻松（Johnson 2026-04-04 凌晨确认）
**口播文案**：第一版已生成（轻松口语风格），Johnson 补充个人信息中（2026-04-04 凌晨主动暂停，等他补充完毕）
**拍摄就绪**：Johnson 说"现在就可以拍"，等他补充完信息后直接开拍
**每日 Dream 汇报**：Johnson 要求每天早上汇报 Dream 结果（已加入日常惯例，2026-04-04 确认）
**Harness优化**：P0权限分级 ✅ + P1双层作用域 ✅ 均已完成（2026-04-04 凌晨，并行执行）
**源码对比分析**：Claude Code源码 + WeChat文章全量重读+分析完成（2026-04-04 凌晨，Johnson 要求直接研究源码）
**起号攻略**（2026-04-04 凌晨研究结论）：
  - 最佳发布时间：12:00-13:00（午休）或 18:00-21:00（下班高峰）
  - 前3秒钩子最关键：提问/反常识/冲突开场
  - 更新频率：日更最佳，养账号权重
  - 互动：主动回复评论，建立粉丝粘性
**Dream状态**：Johnson 要求每天早上汇报 Dream 结果（2026-04-04 确认）
**下一步**：Johnson 补充信息 → 调整文案 → Johnson 审核 → 拍摄 → 素材进流水线

### 第一周选题（E01-E07，2026-04-03 确认）
| 集 | 日期 | 标题 | 类型 | 时长 |
|----|------|------|------|------|
| E01 | 04-03 | 《我叫它大闸蟹》 | 人设亮相 | 30秒 |
| E02 | 04-04 | 《AI最大的bug》 | 痛点共鸣 | 30秒 |
| E03 | 04-05 | 《每天凌晨两点》 | 解法揭示 | 30秒 |
| E04 | 04-06 | 《读报告第一步就错了》 | 方法论 | 45秒 |
| E05 | 04-07 | 《Seedance不用排队》 | 工具评测 | 45秒 |
| E06 | 04-08 | 《一个月前它什么都不记得》 | 成果展示 | 45秒 |
| E07 | 04-09 | 《我在广州和成都各办一场AI嘉年华》 | 活动预告 | 30秒 |

**格式**：真人口播 + Meigen素材穿插，剪辑成一条（情感共鸣先行，非直接介绍）
**脚本存放**：`memory/video-scripts/WEEK1-UNIFIED.md`
**素材状态**：E01-E05 Meigen图已生成（~/Pictures/meigen/），E06/E07待生成

### 流水线分工（2026-04-03 傍晚确认）
- **Johnson**：只负责拍摄原始素材 + 每步审核 + 手动发布
- **大闸蟹**：负责选题→脚本→素材→剪辑全部执行
- **审核节点**：选题 ✅ → 脚本 ✅ → 封面图 ✅ → 剪辑成片 ✅ → Johnson手动发布
- **工具**：ffmpeg v8.0.1（主力）+ Meigen（生图）+ LibTV（视频素材）
- ⚠️ video-editor-ai：VirusTotal 标记 SUSPICIOUS，未安装
- ❌ 剪映：无API/CLI；❌ 视频号API：不对外开放，必须手动发布
- **素材存放**：`~/Videos/大闸蟹视频号/E0x/`（本地Mac，优于飞书云）
- **拍摄规格**：1080p@30fps（视频号输出上限，4K无意义，60fps仅慢动作用）
- **⚠️ 硬规则**：Johnson 说"先XXX" = 只做XXX；素材生成必须等 Johnson 说"可以"

### 流水线文档
- 完整工具清单+审核节点+执行规则：`memory/video-scripts/VIDEO-WORKFLOW.md`

## WeChat 私域引流方案（Johnson 朋友参考，2026-04-03 凌晨）
**场景**：韩国女装抖音直播 → 引流微信私域 → 频繁触发风控
**推荐方案**：
1. **企业微信**（主）：25万客户上限，无需刷脸，需营业执照（个体户即可）
2. **公众号过渡**：引流关注公众号 → 自动回复个人微信 → 添加压力降至1/10
3. **多账号轮转**：每账号每天约30-50人上限，超量等几天激活
4. **养号策略**：新号先用3-4周正常社交，再接引流