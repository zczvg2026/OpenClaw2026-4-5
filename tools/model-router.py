#!/usr/bin/env python3
"""
Model Router for OpenClaw
用法:
  python3 model-router.py minimax    # 切换到 MiniMax M2.7-Lightning
  python3 model-router.py deepseek   # 切换到 DeepSeek V4 Flash
  python3 model-router.py status     # 查看当前模型
  python3 model-router.py toggle     # 在 minimax/deepseek 之间切换
"""

import json
import subprocess
import sys
import os

CONFIG_PATH = os.path.expanduser("~/.openclaw/openclaw.json")
STATE_PATH = os.path.expanduser("~/.openclaw/.model-router-state.json")

MODELS = {
    "minimax": {
        "primary": "minimax-portal/MiniMax-M2.7-Lightning",
        "fallbacks": [
            "minimax-portal/MiniMax-M2.7-highspeed",
            "minimax-portal/MiniMax-M2.7",
        ]
    },
    "deepseek": {
        "primary": "deepseek/deepseek-v4-flash",
        "fallbacks": [
            "deepseek/deepseek-v4-pro",
        ]
    }
}

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def save_config(d):
    # Backup first
    backup = CONFIG_PATH + f".bak.{int(time.time())}"
    with open(backup, 'w') as f:
        json.dump(d, f, indent=2)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(d, f, indent=2)

def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"default": "minimax", "current": "minimax"}

def save_state(s):
    with open(STATE_PATH, 'w') as f:
        json.dump(s, f, indent=2)

def switch_to(model_name):
    """Switch to minimax or deepseek, save return-to default"""
    if model_name not in MODELS:
        print(f"Unknown model: {model_name}. Options: {list(MODELS.keys())}")
        sys.exit(1)
    
    d = load_config()
    state = load_state()
    
    # Save current as "return to" when switching away
    if state["current"] != model_name:
        state["return_to"] = state["current"]
    
    # Update config
    cfg = MODELS[model_name]
    d["agents"]["defaults"]["model"] = {
        "primary": cfg["primary"],
        "fallbacks": cfg["fallbacks"]
    }
    
    state["current"] = model_name
    state["default"] = model_name
    
    save_config(d)
    save_state(state)
    
    # Restart gateway
    subprocess.run(["openclaw", "gateway", "restart"], capture_output=True)
    print(f"✅ 已切换到 {model_name}，Gateway 重启中...")

def switch_back():
    """Switch back to the default model (auto-call after deepseek tasks)"""
    state = load_state()
    if "return_to" in state and state["return_to"]:
        target = state["return_to"]
        print(f"🔄 自动切回 {target}...")
        switch_to(target)
    else:
        switch_to("minimax")

def status():
    state = load_state()
    print(f"当前模型: {state.get('current', 'unknown')}")
    print(f"默认模型: {state.get('default', 'unknown')}")
    print(f"返回目标: {state.get('return_to', 'none')}")

def toggle():
    state = load_state()
    current = state.get("current", "minimax")
    target = "deepseek" if current == "minimax" else "minimax"
    print(f"切换: {current} → {target}")
    switch_to(target)

if __name__ == "__main__":
    import time
    
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "status":
        status()
    elif cmd == "toggle":
        toggle()
    elif cmd == "back":
        switch_back()
    elif cmd in MODELS:
        switch_to(cmd)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)