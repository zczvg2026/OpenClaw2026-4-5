---
scope: private
---

# 关键经验教训

## 【纠正】遇到陌生内容任务，先查专用技能再动手（已复发7次，2026-04-04）
- 微信公众号/任何内容获取任务，**第一步**查 `skills/` 有无对应 parser/scraper，不先用 curl/web_fetch/summarize/浏览器
- 根因：记忆里有条目，但任务来时未触发检索本能。TOOLS.md 已写入规则
- 复发：Johnson 多次说"你又忘了"，mp.weixin.qq.com 文章用了全套10轮失败才想起 wechat-article-parser

## 【反馈】opencli Chrome扩展技术限制（2026-04-04）
- Chrome扩展需图形界面手动安装（Developer Mode → Load unpacked），无法自动化
- opencli daemon 要求 `X-OpenCLI: 1` header，扩展 v1.5.5 没带，导致 Forbidden
- 已有 wechat-article-parser 解决微信文章，opencli非阻塞

## 【反馈】isolated cron 不能主动发飞书消息（2026-04-03深夜）
- isolated session 没有聊天上下文，不知道发给谁
- 需飞书推送的 cron → 必须 main session + systemEvent 触发，不能用 isolated

## 【确认】口播脚本风格：更轻松（2026-04-04）
- 默认轻松口语，少用"我是xxx创始人"，多用真实感受
- 太正式会拉开距离感，轻松风格更适合个人IP视频号

## 【确认】Johnson 要求每天 Dream 汇报（2026-04-04）
- Dream cron 完成后主动向 Johnson 推送一句话总结
- 原因：Johnson 用 Dream 结果作为检查机制

## 【确认+纠正】IMA 日记时间 + 标准流程（2026-04-05 最终确认）
- **时间**：每天晚上 22:30 写，不用早上（Johnson 2026-04-05 下午明确：每天晚上10点半写）
- **完整流程**：飞书预览 → Johnson 确认 → IMA 写入（`import_doc` 渲染不稳定，需双重保险）
- **根因**：一次性 `import_doc` 换行有时保留有时全丢；飞书富文本格式稳定，预览后内容锁定
- **注意**：每天新建一篇独立笔记（`import_doc`），不追加到同一篇
- **换行**：用 heredoc 或 Python 脚本 piping 真实换行符，不在 shell 里手动拼接 JSON
- **脚本**：`~/.openclaw/workspace/skills/ima-note/scripts/write_diary.py`
- 最新 note_id（2026-04-04）：`7446225750071610`

## 【确认】Johnson 要求主动读 IMA 知识库（2026-04-05）
- 涉及 Johnson 公司/行业背景 → 先查 IMA 知识库 → 再结合已掌握信息给判断
- IMA API ClientID: `1d7058d8e7695e4fb7127a168057977e`

## 【纠正】IMA 知识库读取优先级（2026-04-05 07:40）
- 症状：我在 IMA 里乱碰碎片（ENERGY CELL/OpenClaw热潮等），完全没找到 Johnson 真正想让我读的"探迹公司介绍"和"探域公司介绍"
- Why：IMA 里碎片太多，没有先确认优先级就开读，读错方向了
- How to apply：Johnson 给方向 → 先找对应文档 → 再读；IMA 不是用来"全面了解"的，是按需查的

## 【确认】ENERGY CELL 与 域擎 OPC联盟 完全独立（2026-04-05 07:40）
- Johnson 亲口确认：两个项目没有关联，是完全独立的方向
- ENERGY CELL：健康品牌（悠悠富氢水机 + 健康产品）
- 域擎 OPC联盟：商业联盟平台（资料在 IMA）
- 不要再试图找它们的关联

## 【确认】混沌创商院是"实战打磨"场所（2026-04-05）
- Johnson 带真实问题去研讨，不是学知识
- 可引用方法论：单点战略/贝叶斯/右上角理论/破局创新

## 【确认】产品思考三步法固化进工作流（2026-04-05）
- 触发：Johnson 说"帮我看看XX产品/方向/方案"
- 顺序：苏格拉底提问 → 第一性原理 → 奥卡姆剃刀 → 再给结论
- 不能跳过步骤直接输出；出处：抖音 ShaneCodeStudio

## 【确认】Claude Code源码 vs WeChat文章：Harness工程是差距根本（2026-04-04）
- 同一模型，Claude Code harness得78%，其他框架42%
- 能力建设优先 Harness层面（P0权限✅/P1双层作用域✅），不追更强模型

## 【确认】并行任务规则（2026-04-04）
- Johnson 说"都做"→ 直接并行 spawn 两个 subagent，不串行

## 【反馈】auto-backup cron：$(date) 在 crontab 里被预计算（2026-04-04）
- 动态时间变量 cron → 必须写成独立 shell 脚本，cron 只调用脚本路径
- 脚本：`~/.openclaw/auto-backup.sh`

## 【反馈】cron 触发器 ≠ 持久记忆（2026-04-04）
- 所有周期必做任务必须写进 HEARTBEAT.md，不能只依赖 cron 配置

## 【纠正+确认】重复 cron 导致飞书每日噪音（2026-04-05 ✅ 已禁用）
- 症状：cron任务"安装ClawHub技能"（4541798a）每6小时执行→飞书重复推送安装结果，Johnson每日被噪
- Why：任务完成后没有立即禁用cron，留着"以后可能用"导致持续推送
- How to apply：cron任务完成后立即禁用或删除，不要"留着"；定期审计已禁用cron
- **✅ 已禁用**（2026-04-05 22:07）：Gateway 重启后执行 `openclaw cron disable 4541798a-a103-40c2-b4cb-4403380eb31a` 成功
- **教训补充**：`cron disable` 需 Gateway 在运行；Gateway 故障时 disable 静默失败，必须验证 jobs.json 里 `"enabled": false`

## IMA 凭证失效处理（2026-04-04）
- 症状：code 20004 skill auth failed
- 解决：重新生成 Client ID + API Key（服务端吊销，无法预感知）
- 最新 Key（2026-04-04）：`zPNjZeSZJzBVSZ6vanl+/0Dk4khuUaBUFRQaN2/bffjMVjBB2cCWxzh3HLNWA9rey88sTUe3+Q==`

## 飞书文档公网分享（2026-04-04）
- API：`PATCH https://open.feishu.cn/open-apis/drive/v1/permissions/{token}/public?type=docx`
- Body：`{"link_share_entity": "anyone_readable"}`；`type` 放 query 参数，不放 body
