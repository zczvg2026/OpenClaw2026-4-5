#!/bin/bash
# workspace 每日备份：git commit + rsync 快照（保留30份）
# 由 cron 每日 03:00 触发

set -e
WORKSPACE="/Users/mac/.openclaw/workspace"
SNAPSHOT_DIR="/Users/mac/.openclaw/workspace/.backups"
LOG="/Users/mac/.openclaw/workspace/.backups/backup.log"
KEEP=30

mkdir -p "$SNAPSHOT_DIR"

ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(ts)] $1" | tee -a "$LOG"; }

cd "$WORKSPACE"

# 1) git 提交当前变更
log "开始 git commit"
if ! git diff --quiet HEAD 2>/dev/null; then
  git add -A
  if git diff --cached --quiet 2>/dev/null; then
    log "无可提交内容"
  else
    if git commit -m "auto backup $(date '+%Y-%m-%d')" --no-verify >> "$LOG" 2>&1; then
      log "git commit 成功"
    else
      log "git commit 失败（继续快照）"
    fi
  fi
else
  log "工作区干净，跳过 commit"
fi

# 2) rsync 快照到日期目录
SNAP_NAME="$(date '+%Y-%m-%d_%H%M%S')"
SNAP_PATH="$SNAPSHOT_DIR/$SNAP_NAME"
log "开始 rsync -> $SNAP_PATH"

# 排除 .backups 自身和 .git 内的历史对象
rsync -a --delete \
  --exclude=".backups" \
  --exclude=".git/objects/pack/*.tmp" \
  --exclude="node_modules" \
  --exclude="*.pyc" \
  --exclude=".DS_Store" \
  --exclude="cache" \
  --exclude=".cache" \
  "$WORKSPACE/" "$SNAP_PATH/" >> "$LOG" 2>&1

# 3) 清理旧快照（保留最近 KEEP 份）
COUNT=$(ls -1dt "$SNAPSHOT_DIR"/2* 2>/dev/null | wc -l | tr -d ' ')
if [ "$COUNT" -gt "$KEEP" ]; then
  ls -1dt "$SNAPSHOT_DIR"/2* | tail -n +$((KEEP + 1)) | while read -r old; do
    rm -rf "$old"
    log "已清理旧快照: $(basename "$old")"
  done
fi

REMAIN=$(ls -1dt "$SNAPSHOT_DIR"/2* 2>/dev/null | wc -l | tr -d ' ')
log "备份完成，当前保留 $REMAIN 份"
