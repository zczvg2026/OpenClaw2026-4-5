# 飞书信息流 → Obsidian 设计文档

> 状态：实施中
> 最后更新：2026-05-21
> 负责人：大闸蟹（Collect Layer）+ Hermes（Review Layer）

---

## 整体架构

```
飞书群聊/私聊
    │
    ▼ 每4小时 [Collect Layer - 大闸蟹]
┌─────────────────────────────────────┐
│  1. 发现：自动发现新群/私聊           │
│  2. 拉取：全量拉取所有群消息           │
│  3. 去重：按 message_id 去重          │
│  4. 写入：0-raw/feishu-feed/         │
│         YYYY-MM-DD-HH.md            │
└─────────────────────────────────────┘
    │
    ▼ 每日21:00 [Review Layer - Hermes]
┌─────────────────────────────────────┐
│  1. 读取当日 feed                    │
│  2. 转化为原子笔记                    │
│  3. 建立双向链接 wiki                │
│  4. 补全知识链路                      │
└─────────────────────────────────────┘
```

---

## Collect Layer 详细设计

### 1. 目标群/私聊列表（15个）

| Chat ID | 名称 | 类型 |
|---------|------|------|
| oc_bda9eb63f7c1f59bcedb44b84d8a9fef | 广州太擎opc全员群 | 群 |
| oc_ac837cdb3fa033ae89ba34ad6fa67ce2 | 广太大中台 | 群 |
| oc_d71d1e00bbd5c5e47fd7ef7c12770478 | 广太养虾场 | 群 |
| oc_318b873c0b82f03539c07105176be54d | 张承中的claw助手群 | 群 |
| oc_a8e8d101062466423b96210bd4201e51 | 广州太擎opc市级公司群 | 群 |
| oc_f86e8b1b2f9d75fbf5be153ff901c115 | 广州太擎opc社区 | 群 |
| oc_d0a32c96818588653f09e2f36c09348d | 广州太擎opc公会 | 群 |
| oc_c864292aaed2234abe43ce96f544ac75 | Johnson龙虾群 | 群 |
| oc_1a601a4c394b0b870e0a33109c63116f | 域擎智能运营中台 | 群 |
| oc_bbc18cbef48ad3f3618cb685c4ba9d4b | 安宁等多人大私聊 | 私聊 |
| oc_53b92429e5bcd2725329855fa4f7af47 | 渠道管理中心 | 群 |
| oc_b46ae326eb17b66b6727c7a5a1a346cd | 产品开发中心 | 群 |
| oc_17e3b15735c55f67f6c71e8599f8300e | 唐韬/安宁/张承中私聊 | 私聊 |
| oc_c9f9c9eb5a200ca529170a9b9d463334 | OPC 投流 | 群 |
| oc_573e4d6f7a273d98698b8df59a371c7b | 提高成交率项目组 | 群 |

### 2. 定时策略

- **收集频率**：每 4 小时（cron job）
- **时间点**：00:00 / 04:00 / 08:00 / 12:00 / 16:00 / 20:00
- **文件命名**：`YYYY-MM-DD-HH.md`（HH 为整点）
- **去重**：按 `message_id` 去重，每次只拉上次之后的新消息

### 3. Feed 文件格式

```
---
date: 2026-05-21
hour: 08
tags: [feed, feishu, raw]
chat_count: 15
source: lark-cli +chat-messages-list
---

# Feishu Feed 2026-05-21 08:00

## [广州太擎opc全员群] 08:32
- **老王**: 今天日报还没发的注意了，5点之前必须交
- **王鹏**: 收到，肽康的PPT正在做
  - reply: 👍 3

## [私聊-安宁] 08:45
- **安宁**: 客户资料更新了，等你确认后再同步知识库

## [域擎智能运营中台] 08:50
- **老王**: @所有人 明天9点有个会，请大家准时参加

...
```

### 4. 追踪机制

- `memory/feishu-last-fetch.json` - 记录每个 chat 最后拉取的时间戳
- 每次拉取后更新，避免重复拉取

### 5. 新群发现

- 每次 cron 执行时，先调用 `lark-cli im +chat-list` 获取最新群列表
- 对比 `memory/feishu-chats.json` 中的已知群列表
- 新增的群自动加入收集范围

### 6. 错误处理

- 单个群失败不影响其他群
- 失败的群记录到 `memory/feishu-fetch-errors.json`
- 重试逻辑：最多重试 3 次

---

## Review Layer 详细设计（Hermes 负责）

> 见 Hermes 的 Obsidian 任务配置

---

## 文件结构

```
Obsidian Vault/
├── 0-raw/
│   └── feishu-feed/
│       ├── 2026-05-21-00.md
│       ├── 2026-05-21-04.md
│       ├── 2026-05-21-08.md
│       ├── ...
│
├── 1-knowledge/
│   ├── people/           # 人物笔记
│   │   ├── 张承中.md
│   │   ├── 老王.md
│   │   ├── 王鹏.md
│   │   └── ...
│   │
│   ├── project/          # 项目笔记
│   │   ├── 5-30嘉年华.md
│   │   ├── OPC项目.md
│   │   └── ...
│   │
│   ├── concept/          # 概念笔记（卡帕西原子笔记）
│   │   ├── 滴灌营销.md
│   │   ├── 财税智能体.md
│   │   └── ...
│   │
│   └── company/          # 公司/组织笔记
│       ├── 太擎.md
│       ├── 探迹.md
│       └── ...
│
└── memory/
    ├── feishu-chats.json      # 已知群列表
    ├── feishu-last-fetch.json # 最后拉取时间
    └── feishu-fetch-errors.json # 失败记录
```

---

## 技术实现

### Collect Layer 实现

**Cron Job ID**: `FEISHU-COLLECT`（待创建）

**脚本**：`~/.openclaw/workspace/scripts/feishu-feed-collect.sh`

**依赖**：
- `lark-cli im +chat-messages-list`
- `lark-cli im +chat-list`
- Python3（处理去重和写入）

### 消息字段映射

飞书消息 → Feed 文件字段：
- `message_id` → 去重 key
- `chat_id` → 群标识
- `sender.name` → 发消息的人
- `body` → 消息内容
- `create_time` → 时间戳
- `msg_type` → 消息类型（text/image/file 等）

---

## 风险与限制

1. **飞书 API 90天历史限制** - 只能拉近90天消息
2. **Bot 必须已在群中** - 才能拉取该群消息
3. **系统消息**（入群/退群/审批）不在普通消息 API 中
4. **私聊限制** - 只拉 bot 参与的私聊

---

## 下一步

- [ ] 创建 feishu-chats.json（已知群列表）
- [ ] 创建 feishu-feed-collect.sh（收集脚本）
- [ ] 创建 cron job（每4小时触发）
- [ ] 测试单次收集流程
- [ ] 通知 Hermes 配置 Review Layer