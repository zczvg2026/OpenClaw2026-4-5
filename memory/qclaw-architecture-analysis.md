# Qclaw 架构深度分析

> 来源：`~/Library/Application Support/QClaw/` + `~/.qclaw/`
> 分析日期：2026-05-03

## 一句话定位

Qclaw 是一个基于 Electron 封装的 AI 桌面客户端（版本 0.2.14），内嵌 **OpenClaw + Hermes** 双引擎，通过 qclaw-plugin 插件系统提供安全审计、记忆管理、Prompt 优化、任务恢复等 15 个功能模块。

---

## 一、架构总览

```
┌─────────────────────────────────────────────────────┐
│                    QClaw.app                        │
│  Electron 窗口 (Vue3/TS)                             │
├─────────────────────────────────────────────────────┤
│                    qclaw-plugin                      │
│  ┌──────────────┬──────────────┬──────────────────┐  │
│  │   core/       │   packages/   │   tools/         │  │
│  │  • HookProxy  │  (15个)       │  • 安全检查       │  │
│  │  • FetchChain │               │  • 内容审核       │  │
│  │  • ConfigCtr  │               │  • 遥测上报       │  │
│  │  • Reporter   │               │  • SkillHub      │  │
│  │  • GatewayReg │               │                   │  │
│  │  • RouteReg   │               │                   │  │
│  │  • CmdReg     │               │                   │  │
│  └──────────────┴──────────────┴──────────────────┘  │
├─────────────────────────────────────────────────────┤
│           OpenClaw (自建实例)                         │
│           端口 28789 / qclaw 模型 provider             │
├─────────────────────────────────────────────────────┤
│           Hermes Agent (bundled)                     │
│           ~/.hermes/                                 │
├─────────────────────────────────────────────────────┤
│           数据库 (SQLite)                             │
│           qclaw_audit_log / qclaw_config              │
├─────────────────────────────────────────────────────┤
│           配置 (~/.qclaw/)                            │
│           qclaw.json / openclaw.json / 状态目录        │
└─────────────────────────────────────────────────────┘
```

---

## 二、核心框架设计

### 2.1 HookProxy — 事件代理

| 能力 | 说明 |
|------|------|
| 按优先级排序 | priority 数字越小越先执行 |
| Block 语义 | handler 返回 `{ block: true }` 可终止链 |
| Params 改写 | handler 可修改后续 handler 收到的参数 |
| 并发执行 | 相邻 concurrent handler 并行执行 |
| 隔离性 | 单个 handler 异常不影响其他 |
| Append 系统上下文 | 动态注入 system prompt |

### 2.2 FetchChain — 洋葱模型中间件

拦截所有 LLM API 调用，执行的顺序是：

```
Request:  mw1 → mw2 → mw3 → originalFetch
Response: mw3 → mw2 → mw1 → caller
```

关键特性：
- **短路**：onRequest 可返回 shortCircuitResponse，跳过 LLM 调用（如缓存命中）
- **错误恢复**：onError 可返回替代 Response，故障时降级
- **去重**：相同 id 的中间件只保留最新注册的
- **过滤器**：每个中间件可定义 match() 决定是否拦截此请求
- **全局单例**：防 OpenClaw 多次 register() 导致多层嵌套

### 2.3 ConfigCenter — 两层配置

```
fileConfig (qclaw-plugin-config.json)   ← fs.watch 实时监听
    ↓ 覆盖
staticConfig (openclaw.json.pluginConfig)  ← 编译时嵌入
    ↓ 合并
package 通过 ctx.getConfig() 获取
```

- fs.watch + 防抖（300ms）+ TTL（10s）兜底
- 配置变更 → onConfigChange 通知
- Electron 端写入，Gateway 端只读

---

## 三、15 个 Package 详解

### 运行时质量
| Package | 作用 | 启发 |
|---------|------|------|
| **error-response-handler** | HTTP 403/429/500 → 友好中文提示 | 错误不能抛给用户，要变成人话 |
| **cron-delivery-guard** | Cron 投递前校验 to/channel | 先验再投 |
| **workspace-summary** | 会话摘要自动生成（游标增量） | ✓ 已落地 |

### 记忆 & 恢复
| Package | 作用 | 启发 |
|---------|------|------|
| **auto-memory** | Daily-First 记忆提取（游标 + 定时提纯） | ✓ 已落地 |
| **qmemory** | WAL 检查点崩溃恢复 | ✓ 已落地 |

### Prompt & Skill 管理
| Package | 作用 | 启发 |
|---------|------|------|
| **prompt-optimizer** | 按 section 重排/注入 system prompt | 文档已按 ## 分节 |
| **prompt-inspector** | Prompt 内容审计 | — |
| **skill-interceptor** | 权限拦截 + 授权弹窗 | — |
| **skill-usage-analyzer** | 扫描日志分析 skill 使用频次 | 后续可加 |

### 安全 & 合规
| Package | 作用 | 启发 |
|---------|------|------|
| **pcmgr-ai-security** | 风险内容扫描 | — |
| **content-plugin** | 内容审核 + OTLP 遥测 + SkillHub 安装 | — |

### 可观测性
| Package | 作用 | 启发 |
|---------|------|------|
| **trace-span-reporter** | OpenTelemetry Span 上报 | — |
| **agent-browser-reporter** | 浏览器行为上报 | — |
| **data-sync-report** | 数据同步状态上报 | — |

---

## 四、对"大闸蟹"最有价值的 3 个设计

### 1️⃣ 两层配置 + 热更新
不用重启就能改行为。ConfigCenter 用 fs.watch 监听配置文件变更 → 防抖 300ms → 通知所有 package。

**对我**：我的行为可以通过配置文件控制，改配置不用改 prompt。

### 2️⃣ 洋葱模型中间件
请求出去前正序处理，回来后逆序处理。handle 链中的任意一环可以短路、改参数、恢复错误。

**对我**：做每件事前可以走"预处理链"——安全检查→数据准备→执行→后处理→记录。

### 3️⃣ Concurrent + 隔离的 Hook 系统
同一事件（如 agent_end）可以注册多个 handler，并发执行，单 handler 崩溃不影响其他。

**对我**：多步操作可以并行执行，容错性更强。
