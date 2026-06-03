#!/usr/bin/env python3
"""
太擎发票收集主脚本
每周一运行：扫描 hanpaas.dzx@claw.163.com，找出未处理的发票邮件，
解析PDF附件，汇总发邮件到 19108027463@163.com
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ── 配置 ────────────────────────────────────────────────
CONFIG_PATH = "/Users/mac/.openclaw/workspace/invoices/config.json"
STATE_PATH = "/Users/mac/.openclaw/workspace/invoices/state.json"
ATTACH_DIR = Path("/Users/mac/.openclaw/workspace/invoices/attachments")
PROFILE = "dzx"
TARGET_EMAIL = "19108027463@163.com"
SUBJECT_PREFIX = "太擎发票周报"
SCAN_WEEKS = 1  # 扫描最近几周


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_state():
    if Path(STATE_PATH).exists():
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"processedIds": [], "lastScan": None, "invoiceRecords": []}


def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def run_cmd(cmd: list) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout + result.stderr


def is_invoice_subject(subject: str) -> bool:
    """判断主题是否为发票相关"""
    keywords = ["发票", "电子发票", "电子票据", "invoice", "开票", "Invoice", "票"]
    return any(kw in subject for kw in keywords)


def parse_invoice_pdf(pdf_path: str) -> dict:
    """用 pdfplumber 解析发票 PDF"""
    result = {"source": os.path.basename(pdf_path), "raw_file": pdf_path}

    try:
        import pdfplumber

        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"

        if not text.strip():
            result["error"] = "PDF无文字内容（可能是扫描件）"
            return result

        # ── 发票号码 ──
        m = re.search(r"发票号[码号]?[：:\s]*(\w+)", text)
        if m:
            result["invoice_no"] = m.group(1)

        # ── 发票代码 ──
        m = re.search(r"发票代码[：:\s]*(\w+)", text)
        if m:
            result["invoice_code"] = m.group(1)

        # ── 开票日期 ──
        m = re.search(r"开票日期[：:\s]*(\d{4}[-年]\d{1,2}[-月]\d{1,2})", text)
        if m:
            result["date"] = m.group(1).replace("年", "-").replace("月", "-").replace("日", "")

        # ── 销售方 ──
        m = re.search(r"销售方[（(]?名称[）)]?[：:\s]*([^\n\s]{2,30})", text)
        if not m:
            m = re.search(r"销货单位[：:\s]*([^\n\s]{2,30})", text)
        if m:
            result["seller"] = m.group(1).strip()

        # ── 购买方 ──
        m = re.search(r"购买方[（(]?名称[）)]?[：:\s]*([^\n\s]{2,30})", text)
        if not m:
            m = re.search(r"购方名称[：:\s]*([^\n\s]{2,30})", text)
        if m:
            result["buyer"] = m.group(1).strip()

        # ── 金额（不含税） ──
        for pat in [r"金额[（(]?不含税[）)]?[：:\s]*([\d,]+\.?\d*)", r"金额[：:\s]([\d,]+\.?\d*)"]:
            m = re.search(pat, text)
            if m:
                result["amount"] = m.group(1).replace(",", "")
                try:
                    result["amount"] = f"{float(result['amount']):.2f}"
                except ValueError:
                    pass
                break

        # ── 税额 ──
        for pat in [r"税额[：:\s]*([\d,]+\.?\d*)", r"税率[\d%.]+[：:\s]*([\d,]+\.?\d*)"]:
            m = re.search(pat, text)
            if m:
                result["tax"] = m.group(1).replace(",", "")
                try:
                    result["tax"] = f"{float(result['tax']):.2f}"
                except ValueError:
                    pass
                break

        # ── 价税合计 ──
        for pat in [
            r"价税合计[（(]?大写[）)]?[：:\s]*[零壹贰叁肆伍陆柒捌玖拾佰仟万亿兆 ]*([\d,]+\.?\d*)",
            r"价税合计[：:\s]*([\d,]+\.?\d*)",
            r"合计[：:\s]*([\d,]+\.?\d*)",
        ]:
            m = re.search(pat, text)
            if m:
                result["total"] = m.group(1).replace(",", "")
                try:
                    result["total"] = f"{float(result['total']):.2f}"
                except ValueError:
                    pass
                break

        # ── 校验码 ──
        m = re.search(r"校验码[：:\s]*(\w+)", text)
        if m:
            result["check_code"] = m.group(1)

        # 标记关键字段缺失
        required = ["total"]
        missing = [k for k in required if k not in result]
        if missing:
            result["warning"] = f"关键字段未识别: {', '.join(missing)}"

        result["text_preview"] = text[:200]

    except ImportError:
        result["error"] = "pdfplumber 未安装"
    except Exception as e:
        result["error"] = str(e)

    return result


def build_html_table(invoices: list, parsed_results: list) -> str:
    """构建 HTML 邮件正文"""
    valid = [p for p in parsed_results if "error" not in p]
    total_amt = sum(float(p.get("amount", 0) or 0) for p in valid)
    total_tax = sum(float(p.get("tax", 0) or 0) for p in valid)
    total_all = sum(float(p.get("total", 0) or 0) for p in valid)

    rows = ""
    for p, inv in zip(parsed_results, invoices):
        inv_date = inv.get("date", "N/A")
        inv_subject = inv.get("subject", "N/A")
        if "error" in p:
            rows += f"""<tr style="background:#fff0f0;">
                <td>{p.get('source', inv_subject[:20])}</td>
                <td colspan="5" style="color:red">解析失败: {p['error']}</td>
            </tr>"""
        else:
            rows += f"""<tr>
                <td>{p.get('invoice_no', p.get('invoice_code', 'N/A'))}</td>
                <td>{p.get('date', 'N/A')}</td>
                <td>{p.get('seller', 'N/A')}</td>
                <td style="text-align:right">{p.get('amount', 'N/A')}</td>
                <td style="text-align:right">{p.get('tax', 'N/A')}</td>
                <td style="text-align:right"><b>{p.get('total', 'N/A')}</b></td>
            </tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;">
<h2>📄 太擎发票周报</h2>
<p><b>生成时间：</b>{datetime.now().strftime('%Y年%m月%d日 %H:%M')}</p>
<p><b>本期收到发票：</b>{len(parsed_results)} 张（附件含原始PDF）</p>

<h3>汇总</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;width:60%;">
<tr style="background:#f5f5f5;">
    <td><b>项目</b></td>
    <td style="text-align:right"><b>金额（不含税）</b></td>
    <td style="text-align:right"><b>税额</b></td>
    <td style="text-align:right"><b>价税合计</b></td>
</tr>
<tr>
    <td><b>合计</b></td>
    <td style="text-align:right">{total_amt:,.2f}</td>
    <td style="text-align:right">{total_tax:,.2f}</td>
    <td style="text-align:right"><b>{total_all:,.2f}</b></td>
</tr>
</table>

<h3>明细</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;width:100%;">
<tr style="background:#f5f5f5;">
    <th>发票号码</th>
    <th>开票日期</th>
    <th>销售方</th>
    <th style="text-align:right">金额</th>
    <th style="text-align:right">税额</th>
    <th style="text-align:right">价税合计</th>
</tr>
{rows}
</table>

<p style="color:#888;margin-top:24px;font-size:12px;">
本邮件由大闸蟹自动生成，发票PDF原件已作为附件发送。如有解析异常请核查原始邮件。
</p>
</body></html>"""
    return html


def send_email(subject: str, html_body: str, attachments: list):
    """用 mail-cli 发送 HTML 邮件"""
    # 写临时 HTML 文件
    html_file = ATTACH_DIR / "email_body.html"
    with open(html_file, "w") as f:
        f.write(html_body)

    cmd = [
        "mail-cli", "--profile", PROFILE, "compose", "send",
        "--to", TARGET_EMAIL,
        "--subject", subject,
        "--body-file", str(html_file),
        "--html",
    ]
    for att in attachments:
        cmd += ["--attach", att]

    result = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(html_file)
    return result.returncode, result.stdout + result.stderr


def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] === 太擎发票扫描启动 ===")

    config = load_config()
    state = load_state()
    processed_ids = set(state.get("processedIds", []))

    ATTACH_DIR.mkdir(parents=True, exist_ok=True)

    # ── 1. 搜索收件箱发票邮件 ──────────────────────────────
    print(">>> 搜索发票邮件...")
    out = run_cmd(["mail-cli", "--profile", PROFILE, "mail", "search",
                   "--fid", "INBOX", "--keyword", "发票", "--limit", "200", "--json"])

    try:
        messages = json.loads(out).get("data", [])
    except Exception:
        print(f"搜索失败: {out[:200]}")
        messages = []

    # 过滤出未处理且主题含发票关键词的
    new_invoices = []
    for msg in messages:
        mid = msg.get("id", "")
        subject = msg.get("subject", "")
        if mid not in processed_ids and is_invoice_subject(subject):
            new_invoices.append(msg)

    print(f"    共 {len(messages)} 封发票邮件，找到 {len(new_invoices)} 封新发票")

    if not new_invoices:
        print("没有新发票，退出。")
        return

    # ── 2. 逐封处理：下载附件 & 解析 ────────────────────────
    parsed_results = []
    attachments = []
    new_ids = []

    for msg in new_invoices:
        mid = msg["id"]
        subject = msg.get("subject", "")
        new_ids.append(mid)
        print(f"  [{mid}] {subject[:40]}")

        # 获取 MIME 结构
        struct_out = run_cmd(["mail-cli", "--profile", PROFILE, "read", "structure", "--id", mid])
        pdf_parts = []
        for line in struct_out.splitlines():
            part_match = re.match(r"^(\S+)\s+\S+\s+application/pdf\s+", line)
            if part_match:
                pdf_parts.append(part_match.group(1))

        msg_attachments = []
        for part_id in pdf_parts:
            safe_name = f"{mid.replace(':', '_')}_{part_id.replace('.', '_')}.pdf"
            out_file = ATTACH_DIR / safe_name
            result = run_cmd([
                "mail-cli", "--profile", PROFILE, "read", "attachment",
                "--id", mid, "--part", part_id, "--out-file", str(out_file)
            ])
            if out_file.exists() and out_file.stat().st_size > 100:
                print(f"    📎 PDF已下载: {out_file.name} ({out_file.stat().st_size} bytes)")
                msg_attachments.append(str(out_file))
                attachments.append(str(out_file))

        # 解析 PDF
        if msg_attachments:
            for pdf_path in msg_attachments:
                parsed = parse_invoice_pdf(pdf_path)
                parsed["msg_id"] = mid
                parsed["msg_subject"] = subject
                parsed_results.append(parsed)
                print(f"    {'✅' if 'error' not in parsed else '⚠️'} 解析: {parsed.get('invoice_no', parsed.get('error', 'unknown'))}")
        else:
            # 无PDF，只记录邮件信息
            parsed_results.append({
                "msg_id": mid,
                "msg_subject": subject,
                "source": f"邮件: {subject[:30]}",
                "error": "无PDF附件（纯文本邮件）"
            })
            print(f"    ⚠️ 无PDF附件")

    # ── 3. 更新状态 ─────────────────────────────────────────
    state["processedIds"].extend(new_ids)
    state["lastScan"] = datetime.now().isoformat()
    state["invoiceRecords"].extend(parsed_results)
    save_state(state)
    print(f"已更新状态，共处理 {len(new_ids)} 封")

    # ── 4. 发送汇总邮件 ──────────────────────────────────────
    print(f">>> 发送汇总邮件到 {TARGET_EMAIL}...")

    html = build_html_table(new_invoices, parsed_results)
    subject = f"{SUBJECT_PREFIX} - {datetime.now().strftime('%Y-%m-%d')}"

    # 找有效PDF附件（解析成功的）
    valid_attachments = [
        p["raw_file"] for p in parsed_results
        if "error" not in p and p.get("raw_file") and Path(p["raw_file"]).exists()
    ]

    code, output = send_email(subject, html, valid_attachments)

    if code == 0:
        print(f"✅ 邮件发送成功（{len(valid_attachments)} 个PDF附件）")
    else:
        print(f"❌ 邮件发送失败: {output[:200]}")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] === 扫描完成 ===")


if __name__ == "__main__":
    main()