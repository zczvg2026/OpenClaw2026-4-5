# 🦀 飞书 User Token 管理

**目的**：以 Johnson 用户身份调用飞书 API，拉取他所有群消息（不依赖机器人加群）。

## 📁 文件结构

```
.feishu-user/
├── credentials.json       # App ID + App Secret + scopes (chmod 600)
├── user-tokens.json       # access_token + refresh_token (chmod 600) [授权后生成]
├── feishu_user.py         # 主脚本（OAuth + 刷新 + API 调用）
├── .gitignore
└── README.md              # 本文档
```

## 🔑 凭证信息

- **App ID**：`cli_a93eaef757f89bd7`
- **App Secret**：见 `credentials.json`（chmod 600）
- **Owner**：`ou_0b10523c6370a624928ba0e4f1a686b3` (Johnson)
- **重定向**：`http://localhost:8765/callback`
- **Scopes**：
  - `im:message` / `im:message:readonly` — 读消息
  - `im:chat` / `im:chat:readonly` — 读群信息
  - `contact:user.id:readonly` — 读用户 ID

## 🚀 使用

```bash
# 1. 首次授权（一次性，浏览器扫码）
python3 ~/.openclaw/workspace/.feishu-user/feishu_user.py --authorize

# 2. 列出 Johnson 所有群
python3 ~/.openclaw/workspace/.feishu-user/feishu_user.py --list-chats

# 3. 拉某个群最近消息
python3 ~/.openclaw/workspace/.feishu-user/feishu_user.py --list-messages oc_xxx

# 4. 查看 token 状态
python3 ~/.openclaw/workspace/.feishu-user/feishu_user.py --status

# 5. 心跳保活（验证 token 还能用 + refresh_token 周期重置）
python3 ~/.openclaw/workspace/.feishu-user/feishu_user.py --keepalive
```

## ⏰ Token 生命周期 + Keepalive

| Token | 默认有效期 | 续期方式 |
|-------|-----------|---------|
| `access_token` | 2 小时 | `refresh_token` 自动续 |
| `refresh_token` | 30 天 | 重新 OAuth 授权 |

**A+ 策略**（A 主动续期 + B 失败告警）：
- cron `feishu-user-token-keepalive` 每 7 天上午 10 点跑 `--keepalive`
- 成功 → 静默，refresh_token 周期重置到 30 天
- 失败 → 写 `NEEDS_RENEW.json`，下次任何脚本调用时都提醒 Johnson 重授权

**告警机制**：
- 失败时创建 `~/.feishu-user/NEEDS_RENEW.json`（chmod 600）
- `--list-chats` / `--list-messages` 启动时检测到告警文件 → 输出警告

## ⏰ Token 生命周期

| Token | 默认有效期 | 续期方式 |
|-------|-----------|---------|
| `access_token` | 2 小时 | `refresh_token` 自动续 |
| `refresh_token` | 30 天 | 重新 OAuth 授权 |

**策略**：调用前检查 access_token 剩余 < 5 分钟 → 自动 refresh；30 天内不会过期。

## 🔐 安全

- ✅ App Secret / token 文件均 `chmod 600`
- ✅ 目录本身 `chmod 700`
- ✅ `.feishu-user/` 已加入 .gitignore（防误提交）
- ✅ 只申请只读权限，无写权限
- ✅ Johnson 可在飞书开放平台随时撤销授权

## 🦀 创建于 2026-06-01
