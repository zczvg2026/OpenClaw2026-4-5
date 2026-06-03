#!/usr/bin/env python3
"""
failure_distiller.py — 失败轨迹自动蒸馏

功能：
1. 分析对话历史，识别失败/纠正点
2. 蒸馏为结构化 learning 条目
3. 写入 .learnings/distill/ 目录

用法：
    python3 failure_distiller.py                     # 扫描最近会话
    python3 failure_distiller.py --manual "text"    # 手动输入失败情境
    python3 failure_distiller.py --list             # 列出已有 distill 条目
    python3 failure_distiller.py --scan             # 扫描并生成报告
"""

import json
import os
import sys
import re
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

# ============ 配置 ============
WORKSPACE = Path.home() / ".openclaw" / "workspace"
DISTILL_DIR = WORKSPACE / ".learnings" / "distill"
LEARNINGS_MD = WORKSPACE / ".learnings" / "LEARNINGS.md"

# ============ 失败模式定义 ============
FAILURE_PATTERNS = [
    # Johnson 明确否定
    (r"(不对|不对不对|不是这样|错了|你搞错了|重新来)", "explicit_rejection"),
    (r"(等等|停|先别|先等等)", "pause_feedback"),
    # 语气词判断
    (r"算了|不用了|这样不对", "informal_rejection"),
    # 纠正行为
    (r"你应该先|要先.*再|先.*再.*才对", "workflow_correction"),
    # 我不确定时
    (r"不确定|不知道|没查到|可能不对", "uncertainty_acknowledged"),
]

# 好行为模式（用于对比）
GOOD_PATTERNS = [
    (r"好[的得]?", "acknowledged"),
    (r"对[了嘛]?|没问题|可以|行", "explicit_approval"),
    (r"记住了|记下来了", "memory_confirmed"),
    (r"明白了|懂了", "comprehension_confirmed"),
]

# ============ 核心函数 ============

def get_recent_sessions(limit: int = 10):
    """读取最近的 session 历史（从 agents/main/sessions 目录）"""
    sessions_dir = Path.home() / ".openclaw" / "agents" / "main" / "sessions"
    if not sessions_dir.exists():
        return []

    # 读 sessions.json 获取活跃 session 列表
    sessions_json = sessions_dir / "sessions.json"
    active_ids = []
    if sessions_json.exists():
        with open(sessions_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            for key, val in data.items():
                if isinstance(val, dict) and val.get("systemSent"):
                    active_ids.append(val.get("sessionId", ""))

    sessions = []
    for f in sorted(sessions_dir.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True):
        if f.stat().st_size > 1000:  # 过滤空文件
            sessions.append((f, f.stem in active_ids))

    # 优先返回活跃 session
    active = [s for s in sessions if s[1]]
    inactive = [s for s in sessions if not s[1]]
    return (active + inactive)[:limit]


def extract_messages_from_session(session_path: Path, max_messages: int = 200, johnson_only: bool = False):
    """从 session JSONL 文件提取消息（OpenClaw 内部格式）"""
    JOHNSON_OPEN_ID = "ou_0b10523c6370a624928ba0e4f1a686b3"

    def _strip_metadata(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'Conversation info.*?
```\n.*?\n```\n', '', text, flags=re.DOTALL)
        text = re.sub(r'Sender.*?
```\n', '', text, flags=re.DOTALL)
        text = re.sub(r'\[message_id: [^\]]+\]\n?', '', text)
        text = re.sub(r'^(?:张承中|Johnson): ', '', text, flags=re.MULTILINE)
        return text.strip()

    def _is_johnson(text: str) -> bool:
        return JOHNSON_OPEN_ID in text

    messages = []
    try:
        with open(session_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if obj.get("type") == "message":
                        msg = obj.get("message", {})
                        role = msg.get("role", "")
                        if role not in ("user", "assistant"):
                            continue
                        raw = msg.get("content", "")
                        if isinstance(raw, list):
                            raw = " ".join(p.get("text","") for p in raw if isinstance(p, dict) and p.get("type")=="text")
                        elif not isinstance(raw, str):
                            raw = str(raw)
                        if johnson_only and role == "user" and not _is_johnson(raw):
                            continue
                        messages.append({
                            "role": role,
                            "content": raw,
                            "timestamp": obj.get("timestamp", ""),
                            "clean_content": _strip_metadata(raw) if role == "user" else "",
                        })
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"  [warn] 读取 session 失败 {session_path.name}: {e}", file=sys.stderr)
    return messages[-max_messages:]


def classify_failure(text: str) -> Optional[str]:
    """判断文本是否包含失败/纠正信号"""
    for pattern, label in FAILURE_PATTERNS:
        if re.search(pattern, text):
            return label
    return None


def distill_learning(user_msg: str, assistant_msg: str, context: str = "") -> dict:
    """
    蒸馏单条失败轨迹为结构化 learning

    返回:
        dict: {
            "title": str,
            "trigger": str,
            "root_cause": str,
            "behavior_rule": str,
            "checklist": str,
            "filename": str
        }
    """
    # 简单关键词提取
    user_keywords = re.findall(r'[\w]{2,}', user_msg)
    user_keywords = [k for k in user_keywords if len(k) > 3][:5]

    # 生成文件名
    now = datetime.now()
    existing = len(list(DISTILL_DIR.glob("*.md")))
    idx = existing + 1
    filename_slug = f"{now.strftime('%Y%m%d')}-{idx:03d}"
    filename = f"{filename_slug}.md"

    # 生成 title
    title = f"自动蒸馏-{now.strftime('%m%d')}-{idx:03d}"

    return {
        "title": title,
        "trigger": user_msg[:200],
        "root_cause": "（需要人工补充）未做 Eval 自检 / 未先搜索记忆 / 路径含特殊字符",
        "behavior_rule": f"触发条件：收到指令时\n1. 停3秒\n2. 逐条过 Eval\n3. 结论先行\n4. 不确定时说不知道",
        "checklist": f"用户关键词: {', '.join(user_keywords)}\n\n**交付前自检：**\n- [ ] 停3秒再动手\n- [ ] 逐条过 Eval 6条\n- [ ] 先 memory_search 查相关经验\n- [ ] 结论先行\n- [ ] 不确定时说不知道",
        "filename": filename,
        "date": now.strftime("%Y-%m-%d"),
        "user_msg_preview": user_msg[:100],
        "context": context[:200] if context else "",
    }


def write_learning_to_file(learning: dict, dry_run: bool = False) -> Path:
    """将 learning 写入 distill 目录"""
    content = f"""---
date: {learning['date']}
trigger: "{learning['user_msg_preview']}"
source: auto-distilled
tags: [教训, 自动蒸馏]
auto: true
---

# {learning['title']}

## 触发情境
> {learning['trigger']}

{learning['context']}

## 根因
{learning['root_cause']}

## 行为规则

### 触发条件
{learning['behavior_rule'].split('触发条件：')[1] if '触发条件：' in learning['behavior_rule'] else learning['behavior_rule']}

### 违反时的恢复
如果已经交付了错误的回答，立即补充：
> "等等，刚才漏了一步自检，正确答案是……"

## 交付前自检清单
{learning['checklist']}
"""

    filepath = DISTILL_DIR / learning["filename"]

    if dry_run:
        print(f"  [dry-run] 会写入: {filepath}")
        print(f"  内容预览:\n{content[:500]}...")
        return filepath

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  [ok] 写入: {filepath}")
    return filepath


def scan_sessions_for_failures():
    """扫描最近 session，生成失败报告"""
    print("\n🔍 扫描最近 session 寻找失败轨迹...\n")

    sessions = get_recent_sessions(limit=10)
    failures = []

    for session_file, _is_active in sessions:
        messages = extract_messages_from_session(session_file, johnson_only=True)
        active_tag = " [活跃]" if _is_active else ""

        # 逐条检查
        prev_role = None
        prev_content = ""
        for i, msg in enumerate(messages):
            raw = msg.get("content", "")
            clean = msg.get("clean_content", "")
            role = msg.get("role", "")

            # 用清洗后的文本判断failure
            failure_type = classify_failure(clean) or classify_failure(raw)
            if failure_type and role == "user":
                context = f"前一条 assistant: {prev_content[:200]}" if prev_role == "assistant" else ""
                # 用清洗后的文本作为触发文本
                trigger = clean if clean else raw[:200]
                failures.append({
                    "session": session_file.name + active_tag,
                    "msg_idx": i,
                    "type": failure_type,
                    "content": (clean[:300] if clean else raw[:300]),
                    "context": context,
                })

            prev_role = role
            prev_content = clean if clean else raw

    if not failures:
        print("  [info] 未发现明显失败轨迹")
        return

    print(f"  发现 {len(failures)} 条潜在失败轨迹:\n")
    for f in failures:
        print(f"  [{f['type']}] {f['session']}")
        print(f"    {f['content'][:150]}...")
        print()


def list_distill_entries():
    """列出已有哪些自动蒸馏条目"""
    entries = sorted(DISTILL_DIR.glob("*.md"))
    if not entries:
        print("[info] distill 目录为空")
        return

    print(f"\n📚 已有的自动蒸馏条目 ({len(entries)} 条):\n")
    for e in entries:
        print(f"  {e.name}")
    print()



def scan_and_write_failures():
    """扫描 session 并自动将失败轨迹写入 distill/（用于心跳触发）"""
    print("\n🔍 心跳自动蒸馏扫描...")

    sessions = get_recent_sessions(limit=5)
    failures = []

    for session_file, _is_active in sessions:
        messages = extract_messages_from_session(session_file, johnson_only=True)
        active_tag = " [活跃]" if _is_active else ""

        prev_role = None
        prev_content = ""
        for i, msg in enumerate(messages):
            raw = msg.get("content", "")
            clean = msg.get("clean_content", "")
            role = msg.get("role", "")

            failure_type = classify_failure(clean) or classify_failure(raw)
            if failure_type and role == "user":
                context = f"前一条 assistant: {prev_content[:200]}" if prev_role == "assistant" else ""
                trigger = clean if clean else raw[:200]
                failures.append({
                    "session": session_file.name + active_tag,
                    "msg_idx": i,
                    "type": failure_type,
                    "content": (clean[:300] if clean else raw[:300]),
                    "context": context,
                })

            prev_role = role
            prev_content = clean if clean else raw

    if not failures:
        print("  [info] 未发现明显失败轨迹")
        return 0

    print(f"  发现 {len(failures)} 条，自动写入 distill/:")
    written = 0
    for f in failures:
        learning = distill_learning(
            user_msg=f["content"],
            assistant_msg="",
            context=f"来源: {f['session']} | 类型: {f['type']}"
        )
        write_learning_to_file(learning, dry_run=False)
        written += 1

    print(f"  [done] 写入 {written} 条")
    return written
def main():
    parser = argparse.ArgumentParser(description="失败轨迹自动蒸馏工具")
    parser.add_argument("--scan", action="store_true", help="扫描最近 session（仅报告）")
    parser.add_argument("--auto", action="store_true", help="自动蒸馏：扫描 + 写入 distill/")
    parser.add_argument("--list", action="store_true", help="列出已有条目")
    parser.add_argument("--manual", type=str, help="手动输入失败情境")
    parser.add_argument("--dry-run", action="store_true", help="演练模式（不实际写入）")
    args = parser.parse_args()

    DISTILL_DIR.mkdir(parents=True, exist_ok=True)

    if args.list:
        list_distill_entries()
    elif args.auto:
        written = scan_and_write_failures()
    elif args.scan:
        scan_sessions_for_failures()
    elif args.manual:
        # 手动模式：用户输入失败情境，立即蒸馏
        learning = distill_learning(
            user_msg=args.manual,
            assistant_msg="（需补充）",
            context="手动触发"
        )
        write_learning_to_file(learning, dry_run=args.dry_run)
    else:
        # 默认：扫描 + 列出
        scan_sessions_for_failures()
        list_distill_entries()
        print("用法:")
        print("  --scan        扫描最近 session（仅报告）")
        print("  --auto        自动蒸馏：扫描 + 写入 distill/")
        print("  --list        列出已有条目")
        print("  --manual text 手动输入失败情境")
        print("  --dry-run     演练模式")


if __name__ == "__main__":
    main()

