---
scope: private
---

# 工具配置

> 记录已配置好的外部工具/API，供随时调用。

## Meigen.ai（生图）
- **用途**：AI 生图（Nanobanana 2 / Seedream 5.0 / NanoBanana Pro）
- **API token**：`MEIGEN_API_TOKEN=meigen_sk_eUsJyeGZrcZ9e9R2gx5JQNjZLdhiKeeG`（环境变量）
- **调用方式**：`mcporter call creative-toolkit.generate_image`（参数：prompt, aspectRatio, provider）
- **其他工具**：`creative-toolkit.enhance_prompt`、`creative-toolkit.search_gallery`
- **出处**：Johnson 配置（2026-04-02 晚上）

## LibTV（AI 视频）
- **Key**：`sk-libtv-09eabe09c16e4cc08126bad086b23f62`
- **Base URL**：`https://im.liblib.tv/openapi/session`
- **状态**：图片生成 ✅，视频生成需 VIP ❌
- **配置位置**：`~/.openclaw/workspace/skills/libtv-skill/.env`

## NanoBanana Pro（生图）
- **调用**：`mcporter call nano-banana-pro.generate`（参数：prompt, aspectRatio）
- **模型**：Gemini 3 Pro Image
- **配置**：`NANO_BANANA_PRO_API_KEY`（环境变量）

## 飞书
- **工具**：飞书全套集成（会话、日历、知识库、云文档）
- **会话模型配置**：`session_status(model="minimax-m2.5", sessionKey="agent:main:feishu:direct:ou_用户ID")`
- **日历**：`feishu_calendar_*` 系列工具