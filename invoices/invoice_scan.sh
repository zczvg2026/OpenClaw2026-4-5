#!/bin/bash
# 太擎发票扫描工具 - 每周一执行
# 扫描 hanpaas.dzx@claw.163.com 收件箱，识别发票邮件，提取数据，汇总转发

set -euo pipefail

CONFIG="/Users/mac/.openclaw/workspace/invoices/config.json"
STATE_FILE="/Users/mac/.openclaw/workspace/invoices/state.json"
ATTACH_DIR="/Users/mac/.openclaw/workspace/invoices/attachments"
SCRIPT_DIR="/Users/mac/.openclaw/workspace/invoices"

PROFILE=$(jq -r '.sourceProfile' "$CONFIG")
TARGET=$(jq -r '.targetEmail' "$CONFIG")
SUBJECT=$(jq -r '.targetSubject' "$CONFIG")

mkdir -p "$ATTACH_DIR"

echo "=== [$(date)] 太擎发票扫描启动 ==="

# 读取已处理状态
PROCESSED_IDS=$(python3 -c "
import json
with open('$STATE_FILE') as f:
    state = json.load(f)
print(','.join(state.get('processedIds', [])))
")
echo "已处理ID: $PROCESSED_IDS"

# 搜索最近7天的邮件，关键词含"发票"
echo ">>> 搜索发票邮件..."
SEARCH_RESULT=$(mail-cli --profile "$PROFILE" mail search --fid INBOX --keyword "发票" --limit 100 --json 2>/dev/null || echo '{"data":[]}')
echo "$SEARCH_RESULT" | python3 -c "import sys,json; msgs=json.load(sys.stdin).get('data',[]); print(f'找到 {len(msgs)} 封')"

# 提取未处理的发票邮件
NEW_INVOICES=$(echo "$SEARCH_RESULT" | python3 -c "
import json, sys

data = json.load(sys.stdin).get('data', [])
processed = '$PROCESSED_IDS'.split(',') if '$PROCESSED_IDS' else []

results = []
for msg in data:
    mid = msg.get('id', '')
    if mid in processed:
        continue
    # 额外过滤：主题含发票关键词
    subject = msg.get('subject', '')
    if any(kw in subject for kw in ['发票', '电子发票', '电子票据', 'invoice', '开票', 'Invoice']):
        results.append({
            'id': mid,
            'from': msg.get('from', ''),
            'subject': subject,
            'date': msg.get('date', ''),
            'size': msg.get('size', 0)
        })

print(json.dumps(results, ensure_ascii=False, indent=2))
")

NEW_COUNT=$(echo "$NEW_INVOICES" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))")
echo "未处理发票: $NEW_COUNT 封"

if [ "$NEW_COUNT" -eq 0 ]; then
    echo "没有新发票，跳过本轮。"
    exit 0
fi

# 逐封处理：下载附件
INVOICE_DATA="[]"
declare -a ATTACH_PATHS=()

echo ">>> 处理新发票..."
while IFS= read -r row; do
    MSG_ID=$(echo "$row" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
    MSG_SUBJECT=$(echo "$row" | python3 -c "import json,sys; print(json.load(sys.stdin)['subject'])")
    MSG_FROM=$(echo "$row" | python3 -c "import json,sys; print(json.load(sys.stdin)['from'])")
    MSG_DATE=$(echo "$row" | python3 -c "import json,sys; print(json.load(sys.stdin)['date'])")
    
    echo "  [处理] $MSG_SUBJECT ($MSG_ID)"
    
    # 获取邮件结构，找附件
    STRUCT=$(mail-cli --profile "$PROFILE" read structure --id "$MSG_ID" --json 2>/dev/null || echo '{}')
    
    # 检查是否有PDF附件（part type包含application/pdf或文件名含.pdf）
    PDF_PARTS=$(echo "$STRUCT" | python3 -c "
import json, sys
try:
    s = json.load(sys.stdin)
except:
    s = {}
# 结构输出可能是文本格式，尝试找PDF
print('check')
" 2>/dev/null)
    
    # 直接用文本方式读取结构，找PDF附件
    STRUCT_TEXT=$(mail-cli --profile "$PROFILE" read structure --id "$MSG_ID" 2>/dev/null || echo "")
    
    # 解析附件part ID
    PDF_FOUND=false
    while IFS= read -r line; do
        # 跳过第一部分（通常是邮件正文）
        PART_ID=$(echo "$line" | awk '{print $1}' | grep -E '^[0-9]+(\.[0-9]+)*$' || true)
        FILENAME=$(echo "$line" | awk '{$1=""; print $0}' | grep -oiE '[^/]+\.pdf' || true)
        
        if [ -n "$FILENAME" ] && [ -n "$PART_ID" ]; then
            SAFE_NAME=$(basename "$FILENAME" | sed 's/[^a-zA-Z0-9._-]/_/g')
            OUTFILE="$ATTACH_DIR/${MSG_ID}_${SAFE_NAME}"
            
            echo "    下载附件: $FILENAME (part $PART_ID)"
            mail-cli --profile "$PROFILE" read attachment --id "$MSG_ID" --part "$PART_ID" --out-file "$OUTFILE" 2>/dev/null || {
                echo "    下载失败，跳过"
                continue
            }
            
            if [ -f "$OUTFILE" ] && [ -s "$OUTFILE" ]; then
                echo "    已保存: $OUTFILE ($(stat -f%z "$OUTFILE") bytes)"
                ATTACH_PATHS+=("$OUTFILE")
                PDF_FOUND=true
            fi
        fi
    done <<< "$STRUCT_TEXT"
    
    # 如果没有PDF附件，尝试从邮件正文提取发票信息
    if [ "$PDF_FOUND" = false ]; then
        echo "    无PDF附件，尝试从正文提取..."
        BODY=$(mail-cli --profile "$PROFILE" read body --id "$MSG_ID" 2>/dev/null || echo "")
        # 至少记录邮件基本信息
    fi
    
done < <(echo "$NEW_INVOICES" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for item in data:
    print(json.dumps(item, ensure_ascii=False))
")

echo ""
echo ">>> 解析发票PDF..."
PARSED_DATA="[]"
for PDF in "${ATTACH_PATHS[@]}"; do
    echo "  解析: $(basename $PDF)"
    RESULT=$(python3 "$SCRIPT_DIR/parse_invoice.py" "$PDF" 2>/dev/null || echo '{"error": "parse_failed"}')
    echo "    结果: $RESULT"
    PARSED_DATA=$(echo "$PARSED_DATA" | python3 -c "
import json, sys
data = json.load(sys.stdin)
data.append(json.loads('$RESULT'))
print(json.dumps(data, ensure_ascii=False))
")
done

echo ""
echo ">>> 更新已处理状态..."
# 收集本次处理的ID
NEW_IDS=$(echo "$NEW_INVOICES" | python3 -c "
import json, sys
data = json.load(sys.stdin)
ids = [d['id'] for d in data]
print(','.join(ids))
")

python3 -c "
import json
with open('$STATE_FILE') as f:
    state = json.load(f)
new_ids = '$NEW_IDS'.split(',') if '$NEW_IDS' else []
state['processedIds'].extend(new_ids)
state['lastScan'] = '$(date +%Y-%m-%dT%H:%M:%S+08:00)'

# 添加本次发票记录
parsed = json.loads('''$PARSED_DATA''')
new_records = []
for p in parsed:
    if 'error' not in p:
        new_records.append(p)
state['invoiceRecords'].extend(new_records)

with open('$STATE_FILE', 'w') as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
print(f'已更新 {len(new_ids)} 条记录')
"

echo ""
echo ">>> 生成汇总邮件..."

# 构建HTML表格
HTML_TABLE=$(python3 -c "
import json, sys

parsed = json.loads('''$PARSED_DATA''')
rows = ''
for p in parsed:
    if 'error' in p:
        rows += f\"\"\"<tr>
            <td>{p.get('source', 'N/A')}</td>
            <td>{p.get('date', 'N/A')}</td>
            <td colspan='5' style='color:red'>解析失败: {p['error']}</td>
        </tr>
\"\"\"
    else:
        rows += f\"\"\"<tr>
            <td>{p.get('invoice_no', 'N/A')}</td>
            <td>{p.get('date', 'N/A')}</td>
            <td>{p.get('seller', 'N/A')}</td>
            <td style='text-align:right'>{p.get('amount', 'N/A')}</td>
            <td style='text-align:right'>{p.get('tax', 'N/A')}</td>
            <td style='text-align:right'><b>{p.get('total', 'N/A')}</b></td>
            <td>{p.get('buyer', 'N/A')}</td>
        </tr>
\"\"\"

# 统计
valid = [p for p in parsed if 'error' not in p]
total_amt = sum(float(p.get('amount', 0) or 0) for p in valid)
total_tax = sum(float(p.get('tax', 0) or 0) for p in valid)
total_all = sum(float(p.get('total', 0) or 0) for p in valid)

html = f\"\"\"<html>
<head><meta charset='utf-8'></head>
<body style='font-family: sans-serif;'>
<h2>太擎发票周报</h2>
<p>扫描时间: $(date '+%Y年%m月%d日 %H:%M')</p>
<p>本期新增发票: {len(parsed)} 张</p>

<h3>汇总</h3>
<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse; width:100%;'>
<tr style='background:#f0f0f0;'>
    <td><b>项目</b></td>
    <td style='text-align:right'><b>金额（不含税）</b></td>
    <td style='text-align:right'><b>税额</b></td>
    <td style='text-align:right'><b>价税合计</b></td>
</tr>
<tr>
    <td>合计</td>
    <td style='text-align:right'>{total_amt:,.2f}</td>
    <td style='text-align:right'>{total_tax:,.2f}</td>
    <td style='text-align:right'><b>{total_all:,.2f}</b></td>
</tr>
</table>

<h3>明细</h3>
<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse; width:100%;'>
<tr style='background:#f0f0f0;'>
    <th>发票号码</th>
    <th>开票日期</th>
    <th>销售方</th>
    <th>金额</th>
    <th>税额</th>
    <th>价税合计</th>
    <th>购买方</th>
</tr>
{rows}
</table>

<p style='color:#888; margin-top:20px;'>本邮件由大闸蟹自动生成，发票PDF原件已作为附件发送。</p>
</body></html>\"\"\"

print(html)
")

# 构建附件参数
ATTACH_ARGS=""
for p in "${ATTACH_PATHS[@]}"; do
    ATTACH_ARGS="$ATTACH_ARGS --attach $p"
done

# 发送邮件
echo ">>> 发送汇总邮件到 $TARGET ..."
if [ ${#ATTACH_PATHS[@]} -gt 0 ]; then
    echo "$HTML_TABLE" | mail-cli --profile "$PROFILE" compose send \
        --to "$TARGET" \
        --subject "$SUBJECT - $(date '+%Y-%m-%d')" \
        --body-file /dev/stdin \
        --html \
        $ATTACH_ARGS 2>&1
else
    echo "$HTML_TABLE" | mail-cli --profile "$PROFILE" compose send \
        --to "$TARGET" \
        --subject "$SUBJECT - $(date '+%Y-%m-%d')" \
        --body-file /dev/stdin \
        --html 2>&1
fi

SEND_RESULT=$?
if [ $SEND_RESULT -eq 0 ]; then
    echo "✅ 邮件发送成功"
else
    echo "❌ 邮件发送失败 (exit: $SEND_RESULT)"
fi

echo ""
echo "=== [$(date)] 扫描完成 ==="
