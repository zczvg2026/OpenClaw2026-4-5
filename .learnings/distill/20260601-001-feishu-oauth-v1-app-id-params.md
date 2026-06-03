# 20260601-001 飞书 OAuth v1 + app_id 参数踩坑

## 情境
Johnson 让我以他个人身份拉所有飞书群消息（不走机器人），用 user_access_token + OAuth 2.0。

## 踩的 5 个坑
1. OAuth 入口 URL 是 `authen/v1/authorize`，**不是** `authen/v2/authorize`（v2 返回 404）
2. Token 端点是 `authen/v1/access_token`，**不是** `authen/v2/oauth/token`（v2 返回 404）
3. Token 端点需要 **JSON body**，不是 form-urlencoded
4. 飞书 OAuth 用 **`app_id` / `app_secret`**，不是 OAuth 标准的 `client_id` / `client_secret`
5. 成功响应包在 `{"code": 0, "data": {...}}` 里，脚本要展开 `data` 才是 token 字段

## 教训
- 飞书文档站 JS 渲染，web_fetch 拿不到正确路径，**用 curl/python 试 endpoint status 最快**（v1 authorize 200，v2 404）
- OAuth 规范用 client_id/client_secret，但**飞书自创了一套 app_id/app_secret**，不要套通用假设
- 飞书 API 响应统一是 `{code, msg, data}` 三件套，脚本处理必须先 `if code==0: data=data["data"]`
- **OAuth 过程中 code 一次性消耗**，调试中失败多次跑授权时，每次都拿新 code

## 影响范围
- 后续所有飞书 API 调用（im:message, im:chat）都用 `Bearer {access_token}` + `app_id` 不变
- token 1.9 小时过期，refresh_token 30 天，脚本自动续
