# OpenClaw 安全守护机制

> 来源：四十学蒙 - 配置文件安全修改双层守护架构

## 核心问题

AI 代理拥有修改配置的权力，但这也是风险：
- 写错的 JSON 花括号
- 拼错的模型名称
- 可能让整个系统崩溃

## 双层防御架构

### 第一层：fswatch — 铜墙

- 基于 macOS 内核的 kqueue 事件机制
- 配置文件每次被写入，都会在同一秒内检测到
- 纯 JSON 语法校验，不需要模型参与，零 token 消耗
- 语法错误？立即回滚到上一个快照
- 通过 LaunchAgent 注册为系统服务，进程崩溃自动重启

### 第二层：cron 健康巡检 — 铁壁

- 每 5 分钟检查一次 Gateway 是否健康
- 用最轻量的模型（Haiku），每次约 500 token
- 不健康？执行回滚脚本 → 恢复备份 → 重启 Gateway
- 连续 3 次健康？配置稳定确认，自动禁用自身

## 防护矩阵

| 故障类型 | fswatch 能防 | cron 能防 | 恢复时间 |
|---------|-------------|----------|----------|
| JSON 语法错误 | ✅ | 不需要 | < 1 秒 |
| 配置值错误（崩溃） | 语法层看不出 | ✅ | 5~15 分钟 |
| 代理忘记走流程 | ✅ | 需要被启用 | < 1 秒 |

## 安装步骤

```bash
# 1. 安装 fswatch
brew install fswatch

# 2. 安装 config-guardian 技能
clawhub install config-guardian

# 3. 安装 fswatch 守护
cp /Users/mac/.openclaw/workspace/.lib/com.openclaw.config-fswatch-guard.plist /Users/mac/Library/LaunchAgents/
launchctl load /Users/mac/Library/LaunchAgents/com.openclaw.config-fswatch-guard.plist

# 4. 验证
ps aux | grep config-fswatch-guard
```

## 应急手册

如果系统崩溃，执行两行命令：

```bash
python3 /Users/mac/.openclaw/workspace/.lib/config-rollback-guard.py rollback
openclaw gateway restart
```

## 核心理念

> 信任，但要验证。  
> 不，更准确地说：不管信不信任，都要验证。  
> 因为最危险的时刻，恰恰是你觉得"这次不需要验证"的时刻。
