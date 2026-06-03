#!/bin/bash
# 凤凰归巢策略一键运行 v2
# 用法: ./run_strategy.sh [pre_market|intraday|post_market]
set -e

MODE="${1:-post_market}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AKSHARE_VENV="/Users/mac/.venv/aks/bin/python"
TMP_JSON="/tmp/fenghuang-strategy-latest.json"

echo "📍 模式: $MODE"
echo ""

# 管道：AKShare+K线回补 → 策略分析
$AKSHARE_VENV "$SCRIPT_DIR/akshare_feed.py" --mode "$MODE" 2>/dev/null | \
  $AKSHARE_VENV "$SCRIPT_DIR/analyze_phoenix_strategy.py" --input - --format markdown

# 同时保存原始 JSON
$AKSHARE_VENV "$SCRIPT_DIR/akshare_feed.py" --mode "$MODE" 2>/dev/null > "$TMP_JSON"

echo ""
echo "💾 原始数据: $TMP_JSON"
