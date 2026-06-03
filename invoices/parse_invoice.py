#!/usr/bin/env python3
"""
中国电子发票 PDF 解析器
支持：全电发票（PDF）、增值税电子普通发票、增值税电子专用发票
输出结构化 JSON：发票号码、开票日期、销售方、购买方、金额、税额、价税合计
"""

import json
import re
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print(json.dumps({"error": "pdfplumber not installed"}))
    sys.exit(1)


def parse_invoice_text(text: str) -> dict:
    """从 PDF 提取的文本中解析发票字段"""
    result = {}

    # 发票号码 - 多种格式
    patterns = {
        "invoice_no": [
            r"发票号码[：:\s]*(\w+)",
            r"发票代码[：:\s]*(\w+)",
            r"No[：:\s]*(\w+)",
            r"(\d{8,20})",  # 兜底：8-20位数字
        ],
        "date": [
            r"开票日期[：:\s]*([\d\-年/月日\s]+)",
            r"日期[：:\s]*([\d\-年/月日\s]+)",
        ],
        "seller": [
            r"销售方[（(]?名称[）)]?[：:\s]*([^\s\n]+)",
            r"销售方[：:\s]*([^\s\n]+)",
            r"销货单位[：:\s]*([^\s\n]+)",
        ],
        "seller_tax_id": [
            r"销售方[（(]?纳税人识别号[）)]?[：:\s]*(\w+)",
            r"纳税人识别号[：:\s]*(\w+)",
            r"统一社会信用代码[：:\s]*(\w+)",
        ],
        "buyer": [
            r"购买方[（(]?名称[）)]?[：:\s]*([^\s\n]+)",
            r"购买方[：:\s]*([^\s\n]+)",
            r"购货单位[：:\s]*([^\s\n]+)",
            r"购方名称[：:\s]*([^\s\n]+)",
            r"名称[：:\s]*([^\s\n]+)",
        ],
        "amount": [
            r"金额[（(]?不含税[）)]?[：:\s]*([\d,]+\.?\d*)",
            r"金额[：:\s]*([\d,]+\.?\d*)",
            r"小写[（(]?不含税[）)]?[：:\s]*([\d,]+\.?\d*)",
        ],
        "tax": [
            r"税额[：:\s]*([\d,]+\.?\d*)",
            r"税率[：:\s]*[\d%.]+\s*[税额]*[：:\s]*([\d,]+\.?\d*)",
        ],
        "total": [
            r"价税合计[（(]?大写[）)]?[：:\s]*[^0-9]*([\d,]+\.?\d*)",
            r"价税合计[（(]?小写[）)]?[：:\s]*([\d,]+\.?\d*)",
            r"价税合计[：:\s]*([\d,]+\.?\d*)",
            r"合计[：:\s]*([\d,]+\.?\d*)",
            r"总计[：:\s]*([\d,]+\.?\d*)",
        ],
        "check_code": [
            r"校验码[：:\s]*(\w+)",
        ],
    }

    for field, pats in patterns.items():
        for pat in pats:
            m = re.search(pat, text)
            if m:
                val = m.group(1).strip()
                # 清洗日期
                if field == "date":
                    val = val.replace("年", "-").replace("月", "-").replace("日", "")
                # 清洗金额
                if field in ("amount", "tax", "total"):
                    val = val.replace(",", "")
                    try:
                        val = f"{float(val):.2f}"
                    except ValueError:
                        pass
                result[field] = val
                break

    # 如果没找到总额，尝试从文本中提取最后一个金额数字
    if "total" not in result:
        amounts = re.findall(r"([\d,]+\.\d{2})", text)
        if amounts:
            result["total"] = amounts[-1].replace(",", "")

    return result


def extract_text_from_pdf(pdf_path: str) -> str:
    """提取 PDF 所有文本"""
    text_parts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
    except Exception as e:
        # 尝试备用方法
        try:
            import subprocess
            result = subprocess.run(
                ["pdftotext", "-layout", pdf_path, "-"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout
        except Exception:
            pass
        raise
    return "\n".join(text_parts)


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: parse_invoice.py <pdf_path>"}))
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not Path(pdf_path).exists():
        print(json.dumps({"error": f"File not found: {pdf_path}"}))
        sys.exit(1)

    filename = Path(pdf_path).name
    try:
        text = extract_text_from_pdf(pdf_path)
        if not text.strip():
            print(json.dumps({
                "source": filename,
                "error": "No text extracted from PDF",
                "raw_file": pdf_path
            }))
            return

        result = parse_invoice_text(text)
        result["source"] = filename
        result["raw_file"] = pdf_path

        # 标记是否完全解析
        required = ["invoice_no", "total"]
        missing = [k for k in required if k not in result]
        if missing:
            result["warning"] = f"部分字段未识别: {', '.join(missing)}"

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        print(json.dumps({
            "source": filename,
            "error": str(e),
            "raw_file": pdf_path
        }))


if __name__ == "__main__":
    main()
