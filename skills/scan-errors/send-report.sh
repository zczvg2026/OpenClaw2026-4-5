#!/bin/bash
# scan-and-report.sh
# 每天早8:30运行：扫描 + 有问题则推飞书
# 需要配置 FEISHU_WEBHOOK 环境变量（或直接填入）

WORKSPACE="${WORKSPACE:-/Users/mac/.openclaw/workspace}"
SCAN_SCRIPT="$WORKSPACE/skills/scan-errors/scan.js"
REPORTS_DIR="$WORKSPACE/.scan-reports"
TODAY=$(date +%Y-%m-%d)
LOG="$REPORTS_DIR/cron-$TODAY.log"

# 确保报告目录存在
mkdir -p "$REPORTS_DIR"

# 运行扫描
REPORT_TEXT=$(node "$SCAN_SCRIPT" 2>&1)
echo "$REPORT_TEXT" > "$LOG"

# 检查是否有问题（报告里包含 "发现 X 个问题" 且 X > 0）
ISSUES=$(echo "$REPORT_TEXT" | grep -oP '发现 \K\d+(?= 个问题)')
if [ "$ISSUES" != "0" ] && [ -n "$ISSUES" ]; then
  # 有问题，推送飞书
  if [ -n "$FEISHU_WEBHOOK" ]; then
    PAYLOAD=$(cat <<EOF
{
  "msg_type": "text",
  "content": {
    "text": "$REPORT_TEXT"
  }
}
EOF
)
    curl -s -X POST "$FEISHU_WEBHOOK" \
      -H "Content-Type: application/json" \
      -d "$PAYLOAD" > /dev/null
    echo "[$(date)] 已推送飞书，问题数: $ISSUES"
  else
    echo "[$(date)] 有问题但未配置 FEISHU_WEBHOOK，请配置后重试"
  fi
else
  echo "[$(date)] 无问题，不推送"
fi
