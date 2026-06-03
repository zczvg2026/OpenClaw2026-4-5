#!/usr/bin/env python3
"""
飞书信息流收集脚本
每天执行一次：拉取所有群新消息 → 追加到当天的单一一份文件

使用方式: python3 feishu-feed-collect.py
定时: cron job 每天 (推荐 22:00 或更晚)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# lark-cli 配置文件路径（subprocess 需要显式指定）
LARK_CLI_CONFIG_DIR = "/Users/mac/.lark-cli"

def get_lark_env():
    """构建 subprocess 调用的环境变量，避免 lark-cli 找不到配置"""
    env = dict(os.environ)
    env["HOME"] = "/Users/mac"
    env["LARK_CLI_CONFIG_DIR"] = LARK_CLI_CONFIG_DIR
    return env

# ===================== 配置 =====================
OBSIDIAN_VAULT = "/Users/mac/Documents/Obsidian Vault"
FEED_DIR = f"{OBSIDIAN_VAULT}/0-raw/feishu-feed"
MEMORY_DIR = "/Users/mac/.openclaw/workspace/memory"

CHATS_FILE = f"{MEMORY_DIR}/feishu-chats.json"
LAST_FETCH_FILE = f"{MEMORY_DIR}/feishu-last-fetch.json"
ERRORS_FILE = f"{MEMORY_DIR}/feishu-fetch-errors.json"
SEEN_MSGS_FILE = f"{MEMORY_DIR}/feishu-seen-msgs.json"

# ===================== 工具函数 =====================

def load_json(path, default=None):
    if not os.path.exists(path):
        return default if default is not None else {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def now_ts():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# ===================== 核心逻辑 =====================

def fetch_chat_messages(chat_id, chat_name):
    """调用 lark-cli 拉取单个群的消息（最近50条）"""
    import subprocess
    
    cmd = ['lark-cli', 'im', '+chat-messages-list', '--chat-id', chat_id, '--page-size', '50', '--as', 'user']
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=get_lark_env())
        if result.returncode != 0:
            return [], f"lark-cli error: {result.stderr[:100]}"
        
        data = json.loads(result.stdout)
        if not data.get('ok'):
            return [], f"API error: {str(data)[:100]}"
        
        messages = data.get('data', {}).get('messages', [])
        return messages, None
        
    except subprocess.TimeoutExpired:
        return [], "timeout"
    except json.JSONDecodeError as e:
        return [], f"JSON decode error: {e}"
    except Exception as e:
        return [], str(e)

def format_message(msg, chat_name):
    """将单条消息格式化为 feed 条目"""
    sender_obj = msg.get('sender', {})
    sender_type = sender_obj.get('sender_type', '')
    
    if sender_type == 'app':
        sender = 'App消息'
    else:
        sender = sender_obj.get('name', '未知')
    
    msg_type = msg.get('msg_type', 'unknown')
    
    if msg_type == 'text':
        content = msg.get('content', '').strip()
    elif msg_type == 'post':
        try:
            content_json = json.loads(msg.get('content', '[]'))
            text_parts = []
            for segment in content_json:
                if segment.get('tag') == 'text':
                    text_parts.append(segment.get('text', ''))
            content = ''.join(text_parts)[:200] if text_parts else '[富文本帖子]'
        except:
            content = '[富文本帖子]'
    elif msg_type == 'system':
        content = msg.get('content', '')[:100]
    elif msg_type == 'image':
        content = '[图片]'
    elif msg_type == 'file':
        content = '[文件]'
    else:
        content = f'[{msg_type}]'
    
    create_time = msg.get('create_time', '')
    # 转换时间戳
    try:
        ts = int(create_time)
        time_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except:
        time_str = create_time
    
    return {
        'message_id': msg.get('message_id', ''),
        'chat_name': chat_name,
        'chat_id': msg.get('chat_id', ''),
        'sender': sender,
        'time': time_str,
        'content': content,
        'msg_type': msg_type
    }

def discover_new_chats():
    """自动发现新群/私聊"""
    import subprocess
    
    try:
        result = subprocess.run(
            ['lark-cli', 'im', '+chat-list', '--page-size', '100'],
            capture_output=True, text=True, timeout=30,
            env=get_lark_env()
        )
        if result.returncode != 0:
            return [], f"chat-list error: {result.stderr[:100]}"
        
        data = json.loads(result.stdout)
        if not data.get('ok'):
            return [], f"API error: {str(data)[:100]}"
        
        chats = data.get('data', {}).get('chats', [])
        return chats, None
        
    except Exception as e:
        return [], str(e)

def main():
    log("=== 飞书信息流收集开始 ===")
    
    # 1. 加载已知群列表
    if not os.path.exists(CHATS_FILE):
        log(f"错误: 找不到 {CHATS_FILE}")
        sys.exit(1)
    
    chats_data = load_json(CHATS_FILE)
    known_chats = {c['chat_id']: c for c in chats_data.get('chats', [])}
    
    # 2. 自动发现新群
    new_chats, err = discover_new_chats()
    if err:
        log(f"警告: 发现新群失败: {err}")
    else:
        discovered_new = 0
        for nc in new_chats:
            cid = nc.get('chat_id')
            if cid not in known_chats:
                known_chats[cid] = {
                    'chat_id': cid,
                    'name': nc.get('name', '未知'),
                    'type': 'group'
                }
                discovered_new += 1
        
        if discovered_new > 0:
            log(f"发现 {discovered_new} 个新群，已加入监控范围")
            save_json(CHATS_FILE, {
                'chats': list(known_chats.values()),
                'last_updated': now_ts(),
                'note': '通过 lark-cli im +chat-list 自动发现'
            })
    
    # 3. 加载已见过的消息（去重）
    seen_data = load_json(SEEN_MSGS_FILE, default={'message_ids': []})
    seen_msgs = set(seen_data.get('message_ids', []))
    
    # 4. 加载当日已有 feed 内容
    today = datetime.now().strftime("%Y-%m-%d")
    daily_feed_path = f"{FEED_DIR}/{today}.md"
    os.makedirs(FEED_DIR, exist_ok=True)
    
    existing_content = ""
    if os.path.exists(daily_feed_path):
        with open(daily_feed_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    
    # 5. 逐群拉取消息
    new_messages = []
    fetch_errors = []
    
    for chat_id, chat_info in known_chats.items():
        chat_name = chat_info['name']
        log(f"  拉取: {chat_name}")
        
        messages, err = fetch_chat_messages(chat_id, chat_name)
        
        if err:
            log(f"    错误: {err}")
            fetch_errors.append({'chat_id': chat_id, 'chat_name': chat_name, 'error': err})
            continue
        
        for msg in messages:
            msg_id = msg.get('message_id', '')
            if msg_id and msg_id not in seen_msgs:
                seen_msgs.add(msg_id)
                formatted = format_message(msg, chat_name)
                new_messages.append(formatted)
    
    log(f"  新消息: {len(new_messages)} 条")
    
    # 6. 按时间排序
    new_messages.sort(key=lambda x: x['time'] if x['time'] else '')
    
    # 7. 构建当日 feed 内容
    now = datetime.now()
    
    feed_lines = [
        "---",
        f"date: {today}",
        f"collected_at: {now.strftime('%Y-%m-%dT%H:%M:%S+08:00')}",
        "tags: [feed, feishu, daily]",
        f"chat_count: {len(known_chats)}",
        f"new_messages: {len(new_messages)}",
        "source: lark-cli +chat-messages-list",
        "---",
        "",
        f"# Feishu Feed {today}",
        "",
    ]
    
    current_chat = None
    for msg in new_messages:
        if msg['chat_name'] != current_chat:
            current_chat = msg['chat_name']
            feed_lines.append(f"\n## [{current_chat}]")
        
        feed_lines.append(f"- **{msg['sender']}** [{msg['time']}]: {msg['content']}")
    
    if not new_messages:
        feed_lines.append("\n*(今日无新消息)*")
    
    # 8. 写入当日文件（覆盖）
    with open(daily_feed_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(feed_lines))
    
    log(f"  已写入: {daily_feed_path}")
    
    # 9. 更新追踪文件
    save_json(SEEN_MSGS_FILE, {'message_ids': list(seen_msgs)})
    save_json(LAST_FETCH_FILE, {
        'last_fetch': now_ts(),
        'feishu_last_fetch': {cid: now_ts() for cid in known_chats},
        'today_new_messages': len(new_messages),
        'last_errors': fetch_errors[-5:]  # 只保留最近5条错误
    })
    
    log(f"=== 收集完成: {len(new_messages)} 条新消息 ===")

if __name__ == "__main__":
    main()