#!/bin/bash
#===============================================
# OpenClaw Workspace Backup System
# Johnson - 2026-04-04
#===============================================

set -euo pipefail

WORKSPACE="/Users/mac/.openclaw/workspace"
BACKUP_ROOT="/Users/mac/backup/openclaw"      # 本地备份根目录 → 换成你的 NAS/硬盘路径
GIT_BACKUP="$BACKUP_ROOT/git-backup"           # Git 版备份（核心文件）
SNAP_BACKUP="$BACKUP_ROOT/snapshots"           # 快照备份（全量镜像）
LOG="$BACKUP_ROOT/backup.log"
DATE=$(date +%Y-%m-%d_%H%M%S)

OPENCLAW_CONFIG="/Users/mac/.openclaw/openclaw.json"
IMA_CREDS_DIR="/Users/mac/.config/ima"

# 云端 Git 远程（按需填）
# 推荐：GitHub / GitLab / 私有 Git 服务器
GIT_REMOTE=""

# ---- 日志 ----
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"; }

# ---- Exclude patterns for rsync (what NOT to back up) ----
# 大量噪音/可还原的目录和文件
EXCLUDES=(
  "--exclude=MediaCrawler/.venv"
  "--exclude=MediaCrawler/.git"
  "--exclude=MediaCrawler/node_modules"
  "--exclude=MediaCrawler/docs"
  "--exclude=MediaCrawler/browser_data"
  "--exclude=MediaCrawler/output"
  "--exclude=MediaCrawler/logs"
  "--exclude=*/.venv"
  "--exclude=*/node_modules"
  "--exclude=*/.git/objects/pack/*.pack"     # git pack 文件巨大
  "--exclude=*/.git/objects/pack/*.idx"
  "--exclude=*/__pycache__"
  "--exclude=*/.pytest_cache"
  "--exclude=*/dist"
  "--exclude=*/build"
  "--exclude=*.pyc"
  "--exclude=.DS_Store"
  "--exclude=*.pptx"
  "--exclude=*.zip"
  "--exclude=Star-Office-UI-master"
  "--exclude=claw-code-study"
  "--exclude=clawhub_retry*"
  "--exclude=chrome-ext.png"
  "--exclude=docs"
  "--exclude=.clawhub"
  "--exclude=.scan-reports"
  "--exclude=.learnings"
  "--exclude=.openclaw"
  "--exclude=package-lock.json"
  "--exclude=pnpm-lock.yaml"
  "--exclude=package.json"
  "--exclude=tsconfig.json"
)

#===============================================
# 1. 初始化
#===============================================
init() {
  mkdir -p "$BACKUP_ROOT" "$GIT_BACKUP" "$SNAP_BACKUP"
  log "Backup system initialized at $BACKUP_ROOT"
}

#===============================================
# 2. Git 版备份 — 核心文件（~10MB）
#    每天自动 commit，push 到远程
#===============================================
backup_git() {
  log "=== Git backup: core workspace ==="

  # 如果还没有初始化 git 仓库
  if [ ! -d "$GIT_BACKUP/.git" ]; then
    git init "$GIT_BACKUP"
    log "Created new git repo at $GIT_BACKUP"
  fi

  cd "$GIT_BACKUP"

  # 同步核心文件（精确指定，避免漏掉或混入噪音）
  rsync -av \
    --exclude=".DS_Store" \
    --exclude="node_modules" \
    --exclude=".venv" \
    --exclude="package-lock.json" \
    "$WORKSPACE/MEMORY.md" \
    "$WORKSPACE/SOUL.md" \
    "$WORKSPACE/IDENTITY.md" \
    "$WORKSPACE/USER.md" \
    "$WORKSPACE/AGENTS.md" \
    "$WORKSPACE/TOOLS.md" \
    "$WORKSPACE/HEARTBEAT.md" \
    "$WORKSPACE/shared-context/" \
    "$WORKSPACE/memory/" \
    "$WORKSPACE/skills/" \
    "$OPENCLAW_CONFIG" \
    "$IMA_CREDS_DIR/" \
    "$GIT_BACKUP/"

  # 检查是否有变化
  if git diff --quiet && git diff --cached --quiet; then
    log "Git: no changes, skip commit"
  else
    git add -A
    git commit -m "Backup $(date '+%Y-%m-%d %H:%M')"
    log "Git: committed changes"

    if [ -n "$GIT_REMOTE" ]; then
      git push "$GIT_REMOTE" main 2>/dev/null && log "Git: pushed to remote" || log "Git: push failed (check remote)"
    fi
  fi
}

#===============================================
# 3. 快照备份 — 全量镜像（排除噪音）
#    每日增量，保留 30 份快照
#    适合恢复误删文件 / 查看历史版本
#===============================================
backup_snapshot() {
  log "=== Snapshot backup: full workspace ==="

  mkdir -p "$SNAP_BACKUP"

  RSYNC_EXCLUDE_ARGS="${EXCLUDES[*]}"

  rsync -av --delete \
    $RSYNC_EXCLUDE_ARGS \
    "$WORKSPACE/" \
    "$SNAP_BACKUP/current/"

  # 生成带日期的硬链接快照（省空间，原子操作）
  if [ -d "$SNAP_BACKUP/current" ]; then
    cp -al "$SNAP_BACKUP/current" "$SNAP_BACKUP/snapshot_$DATE"
    log "Snapshot created: snapshot_$DATE"
  fi

  # 保留最近 30 份快照，删除更旧的
  SNAP_COUNT=$(ls -1d "$SNAP_BACKUP"/snapshot_* 2>/dev/null | wc -l | tr -d ' ')
  if [ "$SNAP_COUNT" -gt 30 ]; then
    REMOVE_COUNT=$((SNAP_COUNT - 30))
    ls -1dt "$SNAP_BACKUP"/snapshot_* | tail -n "$REMOVE_COUNT" | xargs rm -rf
    log "Pruned $REMOVE_COUNT old snapshots"
  fi
}

#===============================================
# 4. 一键完整备份（手动触发时用）
#===============================================
backup_all() {
  init
  backup_git
  backup_snapshot
  log "=== Full backup complete ==="

  # 输出备份大小
  echo ""
  echo "--- Backup Sizes ---"
  du -sh "$GIT_BACKUP" 2>/dev/null
  du -sh "$SNAP_BACKUP/current" 2>/dev/null
  du -sh "$SNAP_BACKUP" 2>/dev/null
}

#===============================================
# 5. 恢复
#===============================================
restore_git() {
  # 从 git 备份恢复到 workspace
  TARGET=${1:-"$WORKSPACE"}
  log "Restoring git backup to $TARGET"
  rsync -av "$GIT_BACKUP/" "$TARGET/"
  log "Done. Restart OpenClaw to reload."
}

restore_snapshot() {
  SNAPSHOT="$SNAP_BACKUP/snapshot_${1:-latest}"
  if [ ! -d "$SNAPSHOT" ]; then
    echo "Snapshot not found: $SNAPSHOT"
    echo "Available: $(ls $SNAP_BACKUP/snapshot_* 2>/dev/null)"
    exit 1
  fi
  TARGET=${2:-"$WORKSPACE"}
  log "Restoring $SNAPSHOT to $TARGET"
  rsync -av --delete "$SNAPSHOT/" "$TARGET/"
  log "Done."
}

#===============================================
# 6. 状态报告
#===============================================
status() {
  echo "=== OpenClaw Backup Status ==="
  echo ""
  echo "Workspace: $WORKSPACE"
  echo "Git backup: $GIT_BACKUP"
  echo "Snapshots:  $SNAP_BACKUP"
  echo ""
  echo "--- Sizes ---"
  du -sh "$WORKSPACE" 2>/dev/null || echo "n/a"
  du -sh "$GIT_BACKUP" 2>/dev/null || echo "not initialized"
  echo ""
  echo "--- Git Last Commit ---"
  (cd "$GIT_BACKUP" && git log -1 --oneline 2>/dev/null) || echo "no commits"
  echo ""
  echo "--- Snapshots ---"
  ls -1dt "$SNAP_BACKUP"/snapshot_* 2>/dev/null | head -5 || echo "none"
}

#===============================================
# CLI 入口
#===============================================
case "${1:-all}" in
  all)       backup_all ;;
  git)       backup_git ;;
  snapshot)  backup_snapshot ;;
  restore-git)    restore_git "${2:-}" ;;
  restore-snap)   restore_snapshot "${2:-latest}" "${3:-}" ;;
  status)   status ;;
  init)      init ;;
  *)         echo "Usage: $0 {all|git|snapshot|restore-git|restore-snap [date]|status|init}" ;;
esac
