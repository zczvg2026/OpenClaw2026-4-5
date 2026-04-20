# 2026-04-20 对话摘要

## 核心主题
- HeyGen 29个月翻100倍案例学习 → 探讨太擎组织建设
- MiniMax Coding Plan 工具配置完成

## 重要结论

### HeyGen 组织方法论（Johnson 探讨）
- **核心理念**：快速行动、驾驭AI浪潮、双月节奏（跟模型升级同步）
- **决策框架**：99%是双向门决策（产品经理拍板）→ 1%单向门谨慎讨论
- **沟通协议**：异步优先，超过3场/每场超5人的同步会议立即亮红灯
- **最小行动起点**：对齐"未来双月最重要的一件事"，其他全部暂停
- **决策权**：输入宽、决策窄——讨论时全员参与，拍板只有一个人

### 太擎现状（Johnson 自述）
- 团队人员杂
- 问题：方向不清晰、决策慢、执行慢（三者互为因果）

### MiniMax Coding Plan 配置（今日完成）
- API Key: `sk-cp-WH-wzu13cDoZSgILgFka0mIAoRDbeXVZAk6I2xWUIwzQv2HjUTvqnDGaIG_R6aaBQAza63jUv-6oR16wI-KlHNGUCKfwiC2ZhZ16fsfO_o9TcP4X5rLHvXM`
- 配置：`~/.mmx/config.json`（已自动保存）
- 8个工具全部可用（视频需Max Plan，其他7个✅）

### 工具调用优先级（2026-04-20 更新）
1. **mmx CLI**（MiniMax Coding Plan）→ 生图/视频/音乐/搜索/图像理解
2. Gemini → 备选生图
3. Meigen/LibTV → 备选

### 模型切换
- 已切换主模型为 `minimax-portal/MiniMax-M2.7`（之前是 M2.5）
- Gateway 已重启

### IMA 知识库经验（教训）
- 微信文章在 IMA 是 media_type=6（元数据），不是全文
- 正确路径：IMA 找到原文URL → web_fetch 读正文
- 不要一上来就浏览器/web_search，先想工具能力边界

## 待办事项
- [ ] 太擎组织建设：明天开双月对齐会，确认最重要的一件事
- [ ] 视频生成能力需升级到 Max Plan

## 用户偏好
- Johnson 喜欢直接给结论，不绕弯子
- 发现问题立即记录到 TOOLS.md
- 遇到问题先想工具能力边界，不乱试
