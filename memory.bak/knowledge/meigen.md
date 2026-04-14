---
scope: private
---

# Meigen（美拈）- AI 生图平台

## 基本信息
- **网址**：https://www.meigen.ai/
- **定位**：AI 生图提示词画廊 + 一键生成平台
- **模型**：Nanobanana 2、Nanobanana Pro、Seedream 5.0 等
- **API Token**：`MEIGEN_API_TOKEN=meigen_sk_eUsJyeGZrcZ9e9R2gx5JQNjZLdhiKeeG`（环境变量）

## 调用方式（mcporter）
```bash
mcporter call creative-toolkit.generate_image \
  prompt="..." \
  aspectRatio="9:16" \
  provider="meigen"
```

## 辅助工具
- `creative-toolkit.search_gallery` — 搜索灵感画廊
- `creative-toolkit.enhance_prompt` — 优化提示词

## 用途
- 视频号封面图批量生成
- 内容配图
- 灵感参考

## 首次使用记录
- 2026-04-02 晚：第一次测试，生成视频号第一集封面草图
- 生成结果：`https://images.meigen.art/generations/2026-04/f604a864-fa18-4779-94b4-36213d9b08e4.jpg`
- 状态：✅ 成功，Johnson 满意