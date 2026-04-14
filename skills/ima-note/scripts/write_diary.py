#!/usr/bin/env python3
"""
IMA日记写入脚本 - 每天新建一篇笔记
用法: python3 write_diary.py [YYYY-MM-DD]
不传参数默认今天
"""
import os, sys, json, urllib.request
from datetime import datetime

# Load credentials from environment
CLIENT_ID = os.environ.get("IMA_OPENAPI_CLIENTID")
API_KEY = os.environ.get("IMA_OPENAPI_APIKEY")

if not CLIENT_ID or not API_KEY:
    # Fallback: try to read from .zshrc
    zshrc = os.path.expanduser("/Users/mac/.zshrc")
    if os.path.exists(zshrc):
        with open(zshrc) as f:
            for line in f:
                if "IMA_OPENAPI_CLIENTID" in line:
                    CLIENT_ID = line.split('"')[1] if '"' in line else line.split("=")[1].strip()
                if "IMA_OPENAPI_APIKEY" in line:
                    API_KEY = line.split('"')[1] if '"' in line else line.split("=")[1].strip()

if not CLIENT_ID or not API_KEY:
    print("ERROR: IMA credentials not found. Set IMA_OPENAPI_CLIENTID and IMA_OPENAPI_APIKEY")
    sys.exit(1)

def get_diary_content(date_str):
    """生成日记内容 - 读取当日 memory 文件"""
    memory_file = os.path.expanduser(f"/Users/mac/.openclaw/workspace/memory/{date_str}.md")
    if not os.path.exists(memory_file):
        return None
    with open(memory_file) as f:
        raw = f.read()
    # Skip header, return body
    lines = raw.split("\n")
    start = 0
    for i, line in enumerate(lines):
        if line.startswith("---"):
            start = i + 1
            break
    body = "\n".join(lines[start:]).strip()
    return body

def write_diary(date_str):
    content = get_diary_content(date_str)
    if not content:
        print(f"没有找到 {date_str} 的记忆文件")
        sys.exit(1)

    # Format content with proper line breaks using HTML <br>
    # IMA strips \n from markdown, so use <br> for paragraphs
    paragraphs = content.split("\n\n")
    html_content = "<br>".join(p.strip() for p in paragraphs if p.strip())

    payload = json.dumps({
        "content_format": 1,
        "content": f"📅 {date_str} | 大闸蟹日记\n\n{html_content}"
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://ima.qq.com/openapi/note/v1/import_doc",
        data=payload,
        headers={
            "ima-openapi-clientid": CLIENT_ID,
            "ima-openapi-apikey": API_KEY,
            "Content-Type": "application/json; charset=utf-8"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
        if result.get("code") == 0:
            note_id = result["data"]["note_id"]
            print(f"✅ 日记已写入: {note_id}")
            # Save note_id to memory file
            memory_file = os.path.expanduser(f"/Users/mac/.openclaw/workspace/memory/{date_str}.md")
            with open(memory_file, "a") as f:
                f.write(f"\nima_note_id: {note_id}\n")
            return note_id
        else:
            print(f"❌ 失败: {result}")
            sys.exit(1)

if __name__ == "__main__":
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    write_diary(date)
