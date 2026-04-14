# OpenClaw 工具权限分级规范

## 三级权限模型

### L1: 基础会话（飞书/Discord 消息触发）

- **允许**：`memory_search`, `memory_get`, `web_search`, `web_fetch`, `read`, `write`, `edit`
- **禁止**：`exec`, `delete`, `truncate`
- **禁止**：任何文件写入到 `~/.openclaw/` 之外的系统路径
- **限制**：`exec` 仅限查看类命令（`ls`, `cat`, `find`, `git status`）

### L2: 子任务/心跳（cron/subagent）

- 在 L1 基础上：
- **允许**：`exec`（任何读操作，破坏性操作需确认）
- **允许**：`sessions_list`, `sessions_history`（查状态）
- **禁止**：修改 `memory/cron/` 之外的 workspace 核心文件
- **禁止**：删除任何文件

### L3: 信任上下文（init / bootstrap / Johnson 直接指令）

- 全部工具可用
- 破坏性操作（`truncate`, `rm -rf`）需要二次确认
