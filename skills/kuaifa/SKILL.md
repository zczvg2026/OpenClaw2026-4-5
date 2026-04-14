# SKILL.md — Kuaifa 公众号发布

**触发词：** `kuaifa`、`快发`、`发布公众号`、`发到微信`、`发布到微信`、`公众号排版`

**来源：** https://github.com/shirenchuang/kuaifa
**官网：** https://www.kuaifa.art

---

## 是什么

Kuaifa 是一个 CLI 工具，把 Markdown 文章一键发布到微信公众号，自动处理图片上传到微信 CDN。

---

## 核心命令

### 发布文章（默认发草稿）

```bash
kuaifa publish article.md --title "文章标题" --cover cover.jpg
```

| 参数 | 必填 | 说明 |
|---|---|---|
| `<file>` | ✅ | Markdown 文件路径 |
| `--title` | ✅ | 文章标题 |
| `--cover` | ✅ | 封面图（本地路径或 URL） |
| `--author` | ❌ | 作者名（默认取配置） |
| `--digest` | ❌ | 文章摘要 |
| `--template <id>` | ❌ | 模板 ID（默认用配置里的默认模板） |
| `--source-url` | ❌ | "阅读原文"链接 |
| `--draft` | ❌ | 发到草稿箱（**默认行为**） |
| `--send` | ❌ | 直接群发（**不可撤回，慎用**） |

### 发布图文消息（适合图集类）

```bash
kuaifa publish-newspic --title "标题" --images img1.jpg img2.jpg --caption "描述"
```

### 模板管理

```bash
kuaifa template list           # 查看可用模板
kuaifa template prompt <id>    # 获取某个模板的写作规范（生成新文章前必读）
```

### 配置管理

```bash
kuaifa config list             # 查看当前配置
kuaifa config set api-key <key>
kuaifa config set appid <appid>
kuaifa config set appsecret <appsecret>
kuaifa config verify-wechat   # 验证微信凭证
```

### 多账号管理

```bash
kuaifa config profile add <name>       # 新建账号 profile
kuaifa config profile use <name>       # 切换
kuaifa config profile list             # 列出所有
kuaifa --account <name> publish ...     # 临时使用某账号
```

---

## 工作流程

### 写新文章 + 发布

1. 读取模板写作规范：`kuaifa template prompt <template-id>`
2. 按模板规范写 Markdown
3. 发布：`kuaifa publish article.md --title "标题" --cover cover.jpg --template <id>`

### 发布已有文章

直接发布，无需读模板 prompt：

```bash
kuaifa publish article.md --title "标题" --cover cover.jpg
```

---

## 图片处理（自动）

- 本地图片：相对于 Markdown 文件路径解析，也搜索 `assets/` 和 `../assets/`
- 远程图片：自动下载并重新上传到微信 CDN
- 大图自动压缩（>5MB）
- 缓存机制：`.kuaifa-images.json` 记录已上传图片，重复发布跳过再传
- 封面图支持本地路径和 URL

---

## 版本检查

首次使用检查版本，有新版本提醒用户更新：

```bash
kuaifa --version
npm view kuaifa version
npm update -g kuaifa        # 更新 CLI
cd /Users/mac/.openclaw/workspace/skills/kuaifa && git pull  # 更新 skill
```

---

## 常见错误

| 错误 | 解决方法 |
|---|---|
| `kuaifa: command not found` | `npm install -g kuaifa` |
| `未设置 api-key` | 去 kuaifa.art 注册，然后在 `kuaifa config set api-key <key>` |
| `缺少封面图` | 加 `--cover <image>` |
| `缺少文章标题` | 加 `--title "标题"` |
| `微信凭证验证失败` | 去 mp.weixin.qq.com 核对 appid/appsecret |
| 图片上传异常 | 删除 Markdown 同级的 `.kuaifa-images.json` 重试 |

---

## 前置要求

- Node.js >= 18
- kuaifa CLI：`npm install -g kuaifa`
- API 密钥：https://www.kuaifa.art 注册获取
- 微信公众号 AppID / AppSecret
