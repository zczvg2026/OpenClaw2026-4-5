# File Tracking

> Qclaw 文件追踪启发：hash 增量检测文件变更。

## 原理

定期扫描 workspace 核心文件，计算 hash，对比上次记录。
发现变更 → 记录变更日志。

## 命令

```bash
# 扫描并更新
cd ~/.openclaw/workspace
find . -name "*.md" -newer .file-tracking/last-scan 2>/dev/null | head -10

# 查看追踪状态
cat .file-tracking/state.json
```
