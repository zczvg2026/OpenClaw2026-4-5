# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## 工具调用规则（2026-04-20 更新）

**生图顺序（优先用 MiniMax Coding Plan）**
1. **MiniMax Coding Plan（mmx CLI）** → 已配 API Key，直接调用 `mmx image generate`
2. **Gemini（免费）** → `GOOGLE_API_KEY=AIzaSyBJDaSJww8i8PBsrJmF622OYxr_ws0mj-Y`
3. **APIYI** → 备选
4. **MeiGen（mcporter）** → 备选

**mmx CLI 安装和使用（2026-04-20 确认）**
- 安装：`npm install -g mmx-cli`
- 首次配置：`export MINIMAX_API_KEY=<coding-plan-key>` 后运行 `mmx quota show`
- 配置文件：`~/.mmx/config.json`（自动保存）
- 生成图片：`mmx image generate "提示词"`
- 生成视频：`mmx video generate "提示词"`
- 生成音乐：`mmx music generate "提示词"`
- 网页搜索：`mmx search query "关键词"`
- 图像理解：`mmx vision describe <图片路径>`

**生图 → MeiGen（mcporter）**
- 命令：`mcporter call creative-toolkit.generate_image -p "{prompt}" -a {比例} -r {分辨率}`
- 环境变量：`MEIGEN_API_TOKEN=meigen_sk_eUsJyeGZrcZ9e9R2gx5JQNjZLdhiKeeG`
- 模型：`nanobanana-2`（默认）

**生视频 → LibTV**
- Key：`sk-libtv-09eabe09c16e4cc08126bad086b23f62`
- Base URL：`https://im.liblib.tv`
- 注意：Seedance 2.0 需 VIP，可灵等备用

## 时间感知规则（自我约束）

- **不信任 metadata timestamp 做当前时间判断**
- 说"今天/明天/昨天"之前，**必须**执行 `date` 命令或 `session_status` 验证实际时间
- metadata 里的时间只代表"消息发送时间"，不代表 AI 的真实感知时间

## 模型切换规则（2026-05-18 更新）
- **默认模型** → MiniMax M2.7-Lightning（Johnson 明确要求：不指定 DeepSeek 时一律用 MiniMax）
- **编程/写代码** → Johnson 指定时才切 DeepSeek V4 Flash
- 切换方式：当前 session 用 session_status model=xxx 立即生效；永久切换需改 openclaw.json + 重启 gateway
- OpenClaw 升级必须经过 Johnson 确认，不能自己跑
- 当前版本：2026.4.9（通过 npm 安装，LaunchAgent：`ai.openclaw.gateway.new`）

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

## Meigen AI 生图（2026-04-02 确认）
- **网站**：https://www.meigen.ai
- **Token**：`MEIGEN_API_TOKEN=meigen_sk_eUsJyeGZrcZ9e9R2gx5JQNjZLdhiKeeG`（环境变量）
- **调用方式**：`mcporter call creative-toolkit.generate_image`（provider="meigen"）
- **可用工具**：
  - `mcporter call creative-toolkit.generate_image` → 生图
  - `mcporter call creative-toolkit.enhance_prompt` → 优化提示词
  - `mcporter call creative-toolkit.search_gallery` → 搜灵感
- **生成图片本地保存**：`~/Desktop/zczvg/海报文件夹/`（以后所有生图均保存至此）
- **公网 CDN**：`https://images.meigen.art/generations/`
- ⚠️ **教训**：工具配置完成后**立即**写入 TOOLS.md，不要等下次调用时再说

## MiniMax 模型配置（2026-04-12 更新）

**openclaw.json 中的关键配置：**

### 图片理解（MiniMax-VL-01）
- 模型 ID：`MiniMax-VL-01`（`input: ["text", "image"]`）
- 配置路径：`tools.media.image.enabled: true`
- provider：`minimax-portal`
- 踩坑记录：大坑-01（m2.7 默认不支持图片，需配 VL-01）

### TTS（speech-2.8-hd）
- 踩坑记录：坑14（TokenPlan Key 只支持 `-hd`，不支持 `-turbo`）
- 已在 TOOLS.md 中确认用 `speech-2.8-hd`

### 视频查询 URL（坑08）
- 提交：`POST /v1/video_generation`
- 查询：`GET /v1/query/video_generation`（路径不同！）
- LibTV skill 需确认用的是查询 URL 而非提交 URL

---

## IMA 知识库（2026-04-09 配置，2026-04-23 更新凭证）
- **Skill 位置**：`~/.openclaw/workspace/skills/ima-skill-new/`
- **凭证**：`~/.config/ima/`（client_id / api_key）
- **Client ID**：`1d7058d8e7695e4fb7127a168057977e`
- **API Key**（2026-04-04 更新）：`zPNjZeSZJzBVSZ6vanl+/0Dk4khuUaBUFRQaN2/bffjMVjBB2cCWxzh3HLNWA9rey88sTUe3+Q==`
- **验证状态**：✅ 连接正常
- ⚠️ 旧凭证（`5TOHGerHK7cqsvFSH...`）已废弃，以本条为准

---

## ⚠️ 任务执行第一条（必须遵守）

**遇到内容获取任务，第一步查 skills/，第二步再动手！**

**MiniMax 配置教训（2026-04-12）：**
- m2.7 对话模型只有 `input: ["text"]`，无图片理解能力
- 图片理解需单独配 `MiniMax-VL-01`，加到 `models.providers[].models` + `tools.media.image.models`
- openclaw.json 完整模型列表 + tools.media 配置，缺一不可
- 修完后重启 Gateway（SIGUSR1）生效，无需完全重启服务

已翻车3次教训（2026-04-04 × 3）：
- 微信公众号文章 → `skills/wechat-article-parser/` 有专用 parser，别用 curl/web_fetch/浏览器
- 通用方案失败率高，专用工具就在 skills/ 里躺着

---

Add whatever helps you do your job. This is your cheat sheet.

## 抖音内容获取（2026-04-19 已验证）
- **场景**：收到抖音链接，需抓取视频内容/字幕/文案
- **方法**：
  1. `browser action=start profile=openclaw` 启动 openclaw 浏览器（已继承本机 Chrome 登录态）
  2. `browser action=open url=<抖音URL>` 打开视频页面
  3. `screenshot` 截图 → 用 `image` 工具提取画面文字
  4. 配合 `browser action=act` 做点击/滚动等交互
- **注意**：抖音 JS 渲染，直接 curl 抓 HTML 无效，必须走浏览器法

## Mano-P — 桌面 GUI 自动化（2026-05-11 内化）
- **来源**：明略科技开源，微信文章 → Johnson 要求内化
- **项目**：https://github.com/Mininglamp-AI/Mano-P
- **本质**：纯视觉 GUI-VLA 模型，像人一样看屏幕截图操作桌面软件
- **核心能力**：不依赖 CDP/DOM/API，纯视觉驱动，支持桌面软件+浏览器+3D应用
- **本地模式**：M4+32GB Mac，数据不出设备，断网也能跑
- **OSWorld 专项第一**：72B 成功率 58.2%，比第二高 13.2pp
- **Skill 已安装**：`~/.openclaw/workspace/skills/mano-cua/`（来自 ClawHub）
- **二进制安装**：`brew install Mininglamp-AI/tap/mano-cua`（需 Johnson 手动安装，沙箱无 GitHub 访问）
- **使用**：`mano-cua run "任务描述" --local`（本地）或 `mano-cua run "任务描述"`（云端）
- **安装流程**：`mano-cua check` → `mano-cua install-sdk` → `mano-cua install-model`
- **CLI 更多参数**：`--app` 打开指定应用、`--url` 打开指定网页、`--minimize` 最小化面板、`--max-steps` 限制步数
- **大闸蟹可以这样调用**：`python3 /tmp/mano_headless.py "任务描述"`（headless云模式，已验证可用 ✅）
- **二进制安装**：`brew install Mininglamp-AI/tap/mano-cua`（需手动，GUI 在 exec 沙箱不可用，SIGKILL）
- **安装流程**：`mano-cua check` → `mano-cua install-sdk` → `mano-cua install-model`
- **与 OpenClaw 关系**：互补 — OpenClaw 擅长结构化工具调用，Mano-P 擅长桌面 GUI 操控
- ⚠️ 本地模式需 Python 3.13 venv（当前环境 3.9.6，需修复）
