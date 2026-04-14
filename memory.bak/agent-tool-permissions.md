# OpenClaw 工具权限分级方案

> 设计人：大闸蟹 🦀  
> 日期：2026-04-04  
> 版本：v1.0

---

## 一、设计原则

1. **destructive 绝不自动执行** — 任何 destructive 操作必须显式确认
2. **write 操作群聊谨慎** — 群聊中写操作默认需要提示
3. **read-only 自由执行** — 读取类操作无需确认，直接执行
4. **知情同意** — 确认请求必须清晰说明影响范围

---

## 二、工具权限分级表

### 🔵 Level 0 — Read-Only（自由执行，无需确认）

| 工具 | 操作 | 风险说明 |
|------|------|----------|
| `read` | 读取文件内容 | 仅查看，不修改任何数据 |
| `exec` + read-only 命令 | `cat`, `ls`, `pwd`, `head`, `tail`, `grep`, `rg`, `find`(无-delete) | 只读 shell 操作 |
| `web_search` | 搜索网页 | 无副作用 |
| `web_fetch` | 抓取页面内容 | 无副作用 |
| `browser` snapshot/screenshot | 页面快照/截图 | 仅读取，无修改 |
| `image` | 分析图片 | 仅读取，无修改 |
| `pdf` | 分析 PDF | 仅读取，无修改 |
| `tts` | 文字转语音 | 输出到播放设备，无文件修改 |
| `canvas` snapshot | 画布快照 | 仅读取 UI 状态 |
| `feishu_doc` read | 读取飞书文档 | 仅查看 |
| `feishu_wiki` get/spaces/nodes | 读取知识库 | 仅查看 |
| `feishu_bitable_list_records` | 读取多维表格 | 仅查看 |
| `feishu_bitable_get_record` | 读取单条记录 | 仅查看 |
| `feishu_bitable_list_fields` | 读取字段结构 | 仅查看 |
| `feishu_bitable_get_meta` | 解析多维表格 URL | 仅解析 |
| `feishu_chat` info/members | 读取群聊信息 | 仅查看 |
| `feishu_app_scopes` | 读取权限范围 | 仅诊断 |
| `feishu_drive` list/info | 读取云盘内容 | 仅查看 |
| `sessions_yield` | 放弃当前轮次 | 无副作用 |
| `process` list/log | 查看进程状态 | 无修改 |

---

### 🟡 Level 1 — Write（执行前提示，不阻断）

> **规则**：单聊直接执行；群聊中执行前简短提示（可配置关闭）

| 工具 | 操作 | 风险说明 |
|------|------|----------|
| `write` | 覆盖/新建文件 | 修改文件系统，但有覆写保护 |
| `edit` | 编辑文件部分内容 | 修改已有文件 |
| `exec` + 写命令 | `echo`, `tee`, `mkdir`, `touch`, `cp`(非递归) | 有覆写风险，但可恢复 |
| `feishu_doc` write/append/insert | 写入飞书文档 | 修改文档内容 |
| `feishu_doc` create | 创建飞书文档 | 在云端创建资源 |
| `feishu_wiki` create | 创建知识库节点 | 在云端创建资源 |
| `feishu_wiki` rename | 重命名节点 | 云端资源重命名 |
| `feishu_wiki` move | 移动节点 | 云端资源重组 |
| `feishu_bitable_create_record` | 新增多维表格记录 | 云端数据新增 |
| `feishu_bitable_update_record` | 更新记录 | 云端数据修改 |
| `feishu_bitable_create_field` | 新增字段 | 变更多维表格结构 |
| `feishu_bitable_create_app` | 创建多维表格应用 | 云端资源创建 |
| `feishu_drive` create_folder | 创建云盘文件夹 | 云端资源创建 |
| `feishu_drive` move | 移动云盘文件 | 云端资源重组 |
| `message` send | 发送消息 | 向外发送信息（不可撤回） |
| `canvas` present | 展示画布 | UI 展示效果 |

**群聊 Write 提示语示例**：
> ⚠️ 即将写入文件 `project.md`，确认要在群里执行吗？（可回复「继续」跳过提示）

---

### 🔴 Level 2 — Destructive（阻断执行，必须显式确认）

> **规则**：任何情况下绝不自动执行；必须输出确认请求并等待 YES

#### 2.1 文件系统 Destructive

| 工具 | 操作 | 危险程度 | 影响范围 |
|------|------|----------|----------|
| `exec` + `rm` | 删除文件 | ⚠️ 高 | 永久丢失，不可恢复 |
| `exec` + `rm -rf` | 递归强制删除 | 🔥 极高 | 目录及所有子文件永久丢失 |
| `exec` + `mv` 到不安全路径 | 移动覆盖 | ⚠️ 高 | 目标文件被覆盖，不可恢复 |
| `exec` + `dd` | 裸写磁盘 | 🔥 极高 | 可能破坏系统分区 |
| `exec` + `mkfs` | 格式化 | 🔥 极高 | 文件系统清空 |
| `exec` + `kill -9` | 强制终止进程 | ⚠️ 中 | 可能导致数据丢失 |
| `exec` + `pkill -9` | 批量强制终止 | ⚠️ 高 | 批量进程被强杀 |
| `exec` + `shutdown/reboot/halt` | 关机/重启 | ⚠️ 高 | 系统中断 |
| `exec` + `chmod -R 000` | 移除所有权限 | ⚠️ 高 | 文件不可访问 |
| `exec` + `chown` 错误归属 | 修改文件归属 | ⚠️ 中 | 可能导致权限错误 |
| `exec` + `curl/wget` 远程执行 | 下载并执行 | 🔥 极高 | 潜在代码注入 |

#### 2.2 飞书 Destructive

| 工具 | 操作 | 危险程度 | 影响范围 |
|------|------|----------|----------|
| `feishu_doc` delete_block | 删除文档块 | ⚠️ 中 | 内容永久删除（不可逆） |
| `feishu_drive` delete | 删除云盘文件 | ⚠️ 高 | 云端资源永久删除 |
| `feishu_bitable_delete_record` | 删除记录 | ⚠️ 中 | 数据行永久删除 |
| `feishu_bitable_delete_field` | 删除字段 | ⚠️ 高 | 整列数据永久删除 |
| `feishu_bitable_delete_rows` | 批量删除行 | 🔥 极高 | 批量数据永久删除 |
| `feishu_wiki` delete（若支持） | 删除知识库节点 | ⚠️ 高 | 知识库节点永久删除 |
| `feishu_doc` delete_table | 删除表格 | ⚠️ 高 | 表格及数据永久删除 |

#### 2.3 系统级 Destructive

| 工具 | 操作 | 危险程度 | 影响范围 |
|------|------|----------|----------|
| `exec` + 系统管理命令 | `sudo`, `apt-get remove`, `brew remove` 等 | 🔥 极高 | 系统包/应用永久删除 |
| `exec` + 修改 cron/systemd | 篡改定时任务 | 🔥 极高 | 可建立持久化后门 |
| `exec` + 修改 SSH/防火墙 | 改变系统安全配置 | 🔥 极高 | 系统可访问性改变 |
| `exec` + `ssh` 远程命令 | 操控远程机器 | ⚠️ 高 | 远程系统被修改 |
| `exec` + 数据库命令 | `DROP DATABASE`, `DELETE` 大规模 | 🔥 极高 | 数据永久破坏 |
| `exec` + git 强制操作 | `git push --force`, `git reset --hard` | ⚠️ 高 | 版本历史破坏 |

---

## 三、确认流程

### Destructive 操作标准确认模板

```
⚠️ 【destructive 操作确认】

即将执行：<具体操作描述>
影响范围：<具体说明影响的文件/数据/系统>
操作类型：destructive（不可逆）

确认请回复：YES
取消请回复：NO 或任意其他内容

示例确认：YES
```

### 危险命令模式识别规则

以下命令模式自动触发 destructive 确认：

```
# 文件删除类
rm -rf
rm -fr
rm -r
del /f /s /q  (Windows)

# 格式化/分区类
mkfs
mke2fs
format
fdisk

# 覆盖类
> /dev/sdX
dd of=

# 系统级
shutdown
reboot
init 0
init 6

# Git 强制类
git push --force
git reset --hard HEAD~N
git push -f

# 批量删除类
find . -delete
rm $(something)
```

### 确认响应处理

| 用户回复 | 行为 |
|----------|------|
| `YES`（大小写不敏感） | 执行该操作 |
| `YES <comment>` | 执行并记录备注 |
| `NO` 或其他任何内容 | 终止操作，记录取消日志 |
| 超时（5分钟无回复） | 终止操作，提示超时 |

---

## 四、群聊特殊规则

### 群聊 Write 操作默认提示

在群聊中执行 Level 1 (Write) 操作前，发送提示：

```
📝 即将执行：<操作>
影响：<文件/资源名>
群聊中执行，确认继续？回复「继续」跳过提示。
```

### 群聊 Destructive 操作

**群聊中所有 Level 2 操作一律拒绝执行**，并提示：

> 🔴 群聊中不执行 destructive 操作。如需执行，请在私聊中进行。

---

## 五、实施现状（v1.0）

### ✅ 已实现

1. **AGENTS.md 已有规则**：
   - `trash` > `rm`（可恢复优先）
   - destructive 操作前主动询问

2. **本文件记录**：完整权限分级表 + 确认流程 + 规则

### 🚧 待实现（未来版本）

1. **Confirmation Hook**：在 exec 工具层植入 destructive 模式检测，匹配危险命令时自动插入确认流程
2. **飞书消息确认**：实现 `message` 发送前的预览 + 确认机制（尤其是群聊）
3. **HEARTBEAT 集成**：在心跳中检查是否有被取消的 destructive 操作日志
4. **白名单机制**：可配置「信任的命令前缀」，减少重复确认
5. **权限分级可配置**：允许用户在配置文件中调整各工具的风险等级

---

## 六、文件结构

```
memory/
  agent-tool-permissions.md   ← 本文件（主权限规则）
  tool-history/               ← 待建：操作历史记录目录
    YYYY-MM-DD.md             ← 每日 destructive 操作日志
```

---

## 七、快速参考卡

| 级别 | 图标 | 操作 | 行为 |
|------|------|------|------|
| 0 | 🔵 | 读文件、搜索、查看 | 直接执行 |
| 1 | 🟡 | 写文件、发消息 | 单聊直接执行；群聊提示 |
| 2 | 🔴 | 删除文件、系统命令 | **必须 YES 确认** |

**核心规则**：destructive 绝不自动执行。宁可多问一次，不可后悔一次。

---

_🦀 大闸蟹横行天下，安全是第一道防线。_
