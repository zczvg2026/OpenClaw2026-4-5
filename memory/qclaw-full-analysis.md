# Qclaw 完全架构分析

> 第二次深挖（2026-05-03），补全所有角落。

---

## 一、身份与设备系统

4 台已配对设备，全部用 **Ed25519 密钥对**认证：

| 设备 | 平台 | 权限范围 |
|------|------|---------|
| openclaw-control-ui (WebChat) | MacIntel | admin + approvals + pairing |
| CLI × 2 | darwin | admin + read + write + approvals + pairing |
| openclaw-tui (Gateway) | darwin | admin |

每个设备有独立 operator token，作用域精细控制（admin/read/write/approvals/pairing）。

## 二、任务编排系统（tasks/）

SQLite 架构，两张表：

**task_runs**（任务主表）：
- 26 字段：task_id → runtime → status → delivery → notify → cleanup
- 支持父子任务链（parent_flow_id, parent_task_id, child_session_key）
- 进度追踪（progress_summary）和终结状态（terminal_summary, terminal_outcome）
- 定时清理（cleanup_after）

**task_delivery_state**（投递状态）：
- 追踪通知投递到外部渠道的状态

6 个索引覆盖所有查询模式。

## 三、WAL 检查点（qmemory/）

两个真实 checkpoint 文件展示了工作恢复的完整格式：

```json
{
  "taskId": "uuid",
  "agentId": "main",
  "sessionKey": "agent:main:session-xxx",
  "originalPrompt": "用户原始消息",
  "status": "interrupted | running | completed",
  "steps": [
    {
      "toolName": "exec",
      "toolCallId": "exec:29",
      "params": { "command": "..." },
      "seq": 1,
      "status": "completed",
      "startedAt": 1777271051982,
      "result": "...",
      "isError": false,
      "completedAt": 1777271055406
    }
  ],
  "startedAt": ...,
  "updatedAt": ...,
  "endedAt": ...
}
```

特点：
- 每步骤记录 toolName + params + result
- 中断后可查已完成的步骤跳过
- 死（interrupted）/ 活（running）状态分离

## 四、审计日志（SQLite）

```sql
qclaw_audit_log(id, softid, actiontype, detail, risklevel, result, optpath, created_at)
```

42 条记录，actiontype=8（消息查询），risklevel=0，result=1。
简单但有效——每个用户消息都被审计追踪。

## 五、配置进化史

`backups/` 有 **22 个 openclaw.json 备份**（3月20日→4月27日），文件从 2.5KB 增长到 6.7KB：

- 3月20日：初始配置（2.5KB）
- 4月7日：首次重大变更（5.6KB，加了 Qclaw 专属配置）
- 4月20日：插件系统上线（7.9KB，大量新增字段）
- 4月27日：最终版（6.7KB）

见证了 Qclaw 从早期到成熟的演进。

## 六、文件追踪系统

`.qclaw/file_tracking.json`（17KB）：
Qclaw 管理的所有文件的 hash 追踪 + 最后变更时间。用于增量同步和冲突检测。

## 七、同步状态

```json
{
  "agents": { "main": { "hash": "sha256", "lastChangedAt": ... } },
  "identities": {},
  "cronJobs": {},
  "lastReconciliationAt": ...
}
```

基于 hash 的增量同步，只变更 diff。

## 八、Translation Cache

AI Skill 描述的中英文翻译缓存。比如：
```
"AI Agent personality diagnosis..." → "基于MBTI框架的AI智能体人格诊断与配置系统..."
```
按 id 缓存，避免每次翻译。

## 九、Node.js 编译缓存

5 个 Node 版本的 V8 code cache：
- v22.16.0: 3,988 文件
- v22.21.1 × 2: 11,713 + 12,604 文件
- v24.13.0: 562 文件
- v25.7.0: **25,404 文件**（当前主版本）

应用标识后缀（501）表明这些是 Qclaw app 内部 OpenClaw 的缓存。

---

## Qclaw vs 大闸蟹 完整对比

| 维度 | Qclaw | 大闸蟹 |
|------|-------|--------|
| 身份 | Ed25519 密钥对，4设备，operator scopes | 单用户 |
| 任务编排 | SQLite，父子链，delivery，notify | manual |
| 检查点 | qmemory WAL，每步记录 tool + params + result | ✅ 刚做了简化版 |
| 审计 | 每条消息入库 | ❌ 无 |
| 配置热更新 | fs.watch + 两层合并 | ✅ 刚做了 config.json |
| 多模型 | modelroute 路由层 | 单模型切换 |
| 编译缓存 | 25K V8 cache | 不需要 |
| 文件追踪 | hash 增量同步 | ❌ 无 |
| 备份 | 22 个版本自动备份 | ❌ 无 |
| 渠道 | wechat + feishu | feishu |

## 值得再学的 3 个

1. **审计日志**：每条用户消息记录到 SQLite，简单实现但有据可查
2. **文件追踪**：hash 增量同步，适合跨设备
3. **任务编排**：父子链 + 清理策略，适合复杂的多步骤任务
