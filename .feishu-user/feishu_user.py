#!/usr/bin/env python3
"""
飞书 user_access_token 管理 + API 调用
- OAuth 授权（一次性扫码）
- 自动刷新（token 过期前 5 分钟）
- 全量拉群、读消息

设计原则：
- 凭证 600 权限，本地存储
- 只申请只读权限
- token 加密？不加密，但 chmod 600 隔离
"""

import argparse
import http.server
import json
import os
import secrets
import socket
import sys
import time
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

# ==================== 路径配置 ====================
BASE_DIR = Path.home() / ".openclaw/workspace/.feishu-user"
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "user-tokens.json"
PORT = 8765

# ==================== 工具函数 ====================
def load_credentials():
    """加载凭证"""
    if not CREDENTIALS_FILE.exists():
        sys.exit(f"❌ 凭证文件不存在: {CREDENTIALS_FILE}")
    with open(CREDENTIALS_FILE) as f:
        return json.load(f)


def save_tokens(tokens):
    """保存 token 到本地（600 权限）"""
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)
    os.chmod(TOKEN_FILE, 0o600)


def load_tokens():
    """读取 token，如不存在返回 None"""
    if not TOKEN_FILE.exists():
        return None
    with open(TOKEN_FILE) as f:
        return json.load(f)


def http_post(url, data=None, headers=None, form=True):
    """简单 HTTP POST。form=True 用 application/x-www-form-urlencoded（OAuth 用），form=False 用 JSON。"""
    if data is not None and not isinstance(data, (str, bytes)):
        if form:
            data = urllib.parse.urlencode(data).encode()
        else:
            data = json.dumps(data).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    if form:
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    else:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"code": e.code, "msg": f"HTTP {e.code}", "raw": body}


def http_get(url, headers=None):
    """简单 HTTP GET"""
    req = urllib.request.Request(url, method="GET")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"code": e.code, "msg": f"HTTP {e.code}", "raw": body}


# ==================== OAuth 授权流程 ====================
def authorize():
    """启动 OAuth 授权流程，本地起 HTTP server 接住回调"""
    creds = load_credentials()
    app_id = creds["app_id"]
    redirect_uri = creds["redirect_uri"]
    scopes = " ".join(creds["scopes"])

    # state 防 CSRF
    state = secrets.token_urlsafe(16)

    # 飞书 OAuth v1 授权 URL（v2 路径不存在！）
    auth_url = (
        f"https://open.feishu.cn/open-apis/authen/v1/authorize?"
        f"app_id={app_id}&"
        f"redirect_uri={urllib.parse.quote(redirect_uri)}&"
        f"scope={urllib.parse.quote(scopes)}&"
        f"state={state}"
    )

    # 本地 HTTP server 接收回调
    captured_code = {"code": None, "error": None}

    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            if "code" in params:
                captured_code["code"] = params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    "<h1>✅ 授权成功！</h1>"
                    "<p>可以关闭这个窗口了，AI 已经收到授权码。</p>".encode("utf-8")
                )
            else:
                captured_code["error"] = params.get("error", ["unknown"])[0]
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    f"<h1>❌ 授权失败</h1><p>{captured_code['error']}</p>".encode("utf-8")
                )

        def log_message(self, *args):
            # 静默日志
            pass

    # 找空闲端口
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", PORT))
    actual_port = sock.getsockname()[1]
    sock.close()

    # 实际监听
    server = http.server.HTTPServer(("127.0.0.1", actual_port), CallbackHandler)
    server.timeout = 120  # 2 分钟超时

    # 立即输出，不等 flush
    sys.stdout.write("\n")
    sys.stdout.write("🦀 飞书 OAuth 授权启动\n\n")
    sys.stdout.write("👉 请在浏览器中打开以下 URL 并完成授权：\n\n")
    sys.stdout.write(f"   {auth_url}\n\n")
    sys.stdout.write("⏰ 等待授权回调（2 分钟超时）...\n\n")
    sys.stdout.flush()

    # 尝试自动打开浏览器（非阻塞，失败也无所谓）
    try:
        import threading
        def open_browser():
            try:
                webbrowser.open(auth_url)
            except Exception:
                pass
        t = threading.Thread(target=open_browser, daemon=True)
        t.start()
        sys.stdout.write("✅ 已尝试自动打开浏览器（如果没弹，请复制上面的 URL）\n\n")
        sys.stdout.flush()
    except Exception as e:
        sys.stdout.write(f"⚠️  自动打开浏览器失败: {e}\n")
        sys.stdout.write(f"   请手动复制上面的 URL 到浏览器\n\n")
        sys.stdout.flush()

    # 等待回调（最多 120 秒）
    deadline = time.time() + 120
    while time.time() < deadline and captured_code["code"] is None and captured_code["error"] is None:
        server.handle_request()

    server.server_close()

    if captured_code["error"]:
        sys.stdout.write(f"❌ 授权失败: {captured_code['error']}\n")
        sys.stdout.flush()
        sys.exit(1)

    if not captured_code["code"]:
        sys.stdout.write("❌ 授权超时\n")
        sys.stdout.flush()
        sys.exit(1)

    # 用 code 换 token
    sys.stdout.write("✅ 收到授权码，交换 token...\n")
    sys.stdout.flush()

    token_url = "https://open.feishu.cn/open-apis/authen/v1/access_token"
    token_data = {
        "grant_type": "authorization_code",
        "code": captured_code["code"],
        "app_id": app_id,
        "app_secret": creds["app_secret"],
        "redirect_uri": redirect_uri,
    }

    result = http_post(token_url, token_data, form=False)  # 飞书 v1 access_token 需要 JSON

    # 飞书 API 响应包在 {"code": 0, "data": {...}} 里，需要提取
    if result.get("code") == 0 and "data" in result:
        result = result["data"]

    if "access_token" not in result:
        sys.stdout.write(f"❌ 换取 token 失败: {json.dumps(result, ensure_ascii=False, indent=2)}\n")
        sys.stdout.flush()
        sys.exit(1)

    # 加上过期时间戳
    result["expires_at"] = int(time.time()) + result.get("expires_in", 7200)
    result["refresh_expires_at"] = int(time.time()) + result.get("refresh_expires_in", 2592000)
    result["authorized_at"] = int(time.time())

    save_tokens(result)

    sys.stdout.write("\n")
    sys.stdout.write(f"✅ 授权完成！token 已保存到 {TOKEN_FILE}\n")
    sys.stdout.write(f"   有效期: {result['expires_in']} 秒\n")
    sys.stdout.write(f"   refresh_token 有效期: {result.get('refresh_expires_in', 2592000)} 秒 ({result.get('refresh_expires_in', 2592000) // 86400} 天)\n")
    sys.stdout.write("\n")
    sys.stdout.write("🦀 接下来可以执行: python3 feishu_user.py --list-chats\n")
    sys.stdout.flush()


# ==================== Token 刷新 ====================
def get_valid_token():
    """获取有效的 access_token，过期前自动刷新"""
    tokens = load_tokens()
    if not tokens:
        sys.exit("❌ 还没有授权，请先执行: python3 feishu_user.py --authorize")

    now = int(time.time())
    # 提前 5 分钟刷新
    if now < tokens.get("expires_at", 0) - 300:
        return tokens["access_token"]

    print("🔄 access_token 即将过期，刷新中...")

    creds = load_credentials()
    refresh_url = "https://open.feishu.cn/open-apis/authen/v1/access_token"
    refresh_data = {
        "grant_type": "refresh_token",
        "refresh_token": tokens["refresh_token"],
        "app_id": creds["app_id"],
        "app_secret": creds["app_secret"],
    }

    result = http_post(refresh_url, refresh_data, form=False)  # JSON

    # 飞书 API 响应包在 {"code": 0, "data": {...}} 里
    if result.get("code") == 0 and "data" in result:
        result = result["data"]

    if "access_token" not in result:
        sys.exit(f"❌ 刷新失败: {json.dumps(result, ensure_ascii=False, indent=2)}\n💡 重新授权: python3 feishu_user.py --authorize")

    result["expires_at"] = int(time.time()) + result.get("expires_in", 7200)
    result["refresh_expires_at"] = int(time.time()) + result.get("refresh_expires_in", 2592000)
    save_tokens(result)

    print(f"✅ token 已刷新")
    return result["access_token"]


# ==================== API 调用 ====================
def list_chats():
    """列出 Johnson 所有群"""
    token = get_valid_token()
    url = "https://open.feishu.cn/open-apis/im/v1/chats?page_size=100"
    headers = {"Authorization": f"Bearer {token}"}

    all_chats = []
    page_token = None

    while True:
        u = url + (f"&page_token={page_token}" if page_token else "")
        result = http_get(u, headers)

        if result.get("code") != 0:
            print(f"❌ API 错误: {json.dumps(result, ensure_ascii=False, indent=2)}")
            sys.exit(1)

        chats = result.get("data", {}).get("items", [])
        all_chats.extend(chats)

        if not result.get("data", {}).get("has_more", False):
            break
        page_token = result["data"].get("page_token")

    print(f"")
    print(f"🦀 共找到 {len(all_chats)} 个群")
    print(f"")
    for c in all_chats:
        chat_id = c.get("chat_id", "")
        name = c.get("name", "(无名称)")
        chat_mode = c.get("chat_mode", "?")
        # p2p=私聊 group=群聊 thread=话题
        type_map = {"p2p": "私聊", "group": "群聊", "thread": "话题"}
        type_cn = type_map.get(chat_mode, chat_mode)
        print(f"  [{type_cn:>4}] {name:30s}  {chat_id}")

    # 保存到本地归档
    archive_dir = Path.home() / ".openclaw/workspace/memory/feishu-chats"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_file = archive_dir / "chats.json"
    with open(archive_file, "w") as f:
        json.dump({
            "fetched_at": int(time.time()),
            "count": len(all_chats),
            "chats": all_chats,
        }, f, ensure_ascii=False, indent=2)
    os.chmod(archive_file, 0o600)
    print(f"")
    print(f"📁 已归档到: {archive_file}")

    return all_chats


def list_messages(chat_id, count=20):
    """列出指定群最近 N 条消息"""
    token = get_valid_token()
    url = f"https://open.feishu.cn/open-apis/im/v1/messages?container_id_type=chat&container_id={chat_id}&page_size={count}"
    headers = {"Authorization": f"Bearer {token}"}

    result = http_get(url, headers)

    if result.get("code") != 0:
        print(f"❌ API 错误: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return None

    items = result.get("data", {}).get("items", [])
    print(f"")
    print(f"🦀 最近 {len(items)} 条消息")
    print(f"")

    for m in items:
        sender = m.get("sender", {}).get("id", "?")
        msg_type = m.get("msg_type", "?")
        create_time = m.get("create_time", "")
        # 时间戳转可读
        if create_time:
            try:
                from datetime import datetime
                dt = datetime.fromtimestamp(int(create_time) / 1000)
                ts_str = dt.strftime("%m-%d %H:%M")
            except:
                ts_str = create_time
        else:
            ts_str = "?"

        # 提取文本内容
        body = m.get("body", {}).get("content", "")
        try:
            body_data = json.loads(body)
            text = body_data.get("text", body)[:200]
        except:
            text = body[:200]

        print(f"  [{ts_str}] {sender[:15]:15s} | {text}")

    return items


# ==================== Keepalive ====================
def check_alert():
    """启动时检查是否有需要重新授权的告警"""
    if ALERT_FILE.exists():
        try:
            with open(ALERT_FILE) as f:
                alert = json.load(f)
            print(f"")
            print(f"⚠️  【告警】飞书 user_access_token 已失效")
            print(f"   原因: {alert.get('detail', 'unknown')}")
            print(f"   时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert.get('ts', 0)))}")
            print(f"   解决: python3 ~/.openclaw/workspace/.feishu-user/feishu_user.py --authorize")
            print(f"")
        except Exception:
            pass


# ==================== Keepalive ====================
ALERT_FILE = Path.home() / ".openclaw/workspace/.feishu-user/NEEDS_RENEW.json"
KEEPALIVE_LOG = Path.home() / ".openclaw/workspace/memory/feishu-chats/keepalive.log"


def keepalive():
    """心跳保活：调用 get_valid_token() + 拉 1 个群，验证 token 还能用。
    成功 -> 写 keepalive.log，refresh_token 周期重置到 30 天
    失败 -> 写 NEEDS_RENEW.json，下次任何脚本被调用时 main session 会看到
    """
    ok = False
    detail = ""
    try:
        # 1. 拿 access_token (会触发 refresh)
        token = get_valid_token()
        # 2. 拿一下 user profile 验证 token 真实有效
        url = "https://open.feishu.cn/open-apis/authen/v1/user_info"
        result = http_get(url, {"Authorization": f"Bearer {token}"})

        if result.get("code") == 0:
            user = result.get("data", {})
            name = user.get("name", "unknown")
            ok = True
            detail = f"token 有效，用户={name}"
        else:
            detail = f"user_info API 错误: {result.get('code')} {result.get('msg', '')}"
    except SystemExit as e:
        detail = f"token 不可用: {str(e)}"
    except Exception as e:
        detail = f"未知错误: {type(e).__name__}: {e}"

    # 写日志
    KEEPALIVE_LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))} {'OK' if ok else 'FAIL'} {detail}\n"
    with open(KEEPALIVE_LOG, "a") as f:
        f.write(line)

    if ok:
        # 成功：删掉告警标志
        if ALERT_FILE.exists():
            ALERT_FILE.unlink()
        print(f"✅ {detail}")
        # 写当前 token 剩余时间
        tokens = load_tokens()
        if tokens:
            access_left = (tokens.get("expires_at", 0) - ts) // 60
            refresh_left = (tokens.get("refresh_expires_at", 0) - ts) // 86400
            print(f"   access_token 剩余: {access_left} 分钟")
            print(f"   refresh_token 剩余: {refresh_left} 天")
        sys.exit(0)
    else:
        # 失败：写告警标志
        ALERT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(ALERT_FILE, "w") as f:
            json.dump({
                "ts": ts,
                "detail": detail,
                "action": "需要 Johnson 重新执行 OAuth 授权"
            }, f, ensure_ascii=False, indent=2)
        os.chmod(ALERT_FILE, 0o600)
        print(f"❌ {detail}", file=sys.stderr)
        print(f"⚠️  已写告警标志: {ALERT_FILE}", file=sys.stderr)
        sys.exit(1)


# ==================== CLI 入口 ====================
def main():
    parser = argparse.ArgumentParser(
        description="🦀 飞书 user_access_token 管理 + API 工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 feishu_user.py --authorize       # 首次 OAuth 授权
  python3 feishu_user.py --list-chats      # 列出你所有群
  python3 feishu_user.py --list-messages oc_xxx  # 拉某个群的消息
  python3 feishu_user.py --status          # 查看 token 状态
        """,
    )
    parser.add_argument("--authorize", action="store_true", help="启动 OAuth 授权流程")
    parser.add_argument("--list-chats", action="store_true", help="列出我所在的所有群")
    parser.add_argument("--list-messages", metavar="CHAT_ID", help="拉取某群最近消息")
    parser.add_argument("--count", type=int, default=20, help="消息数（默认 20）")
    parser.add_argument("--status", action="store_true", help="查看 token 状态")
    parser.add_argument("--keepalive", action="store_true", help="心跳保活：验证 token 还能用")

    args = parser.parse_args()

    if args.authorize:
        authorize()
    elif args.list_chats:
        check_alert()
        list_chats()
    elif args.list_messages:
        check_alert()
        list_messages(args.list_messages, args.count)
    elif args.keepalive:
        keepalive()
    elif args.status:
        tokens = load_tokens()
        if not tokens:
            print("❌ 未授权")
            return
        now = int(time.time())
        expires_in = tokens.get("expires_at", 0) - now
        refresh_in = tokens.get("refresh_expires_at", 0) - now
        print(f"🦀 Token 状态")
        print(f"   授权时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tokens.get('authorized_at', 0)))}")
        print(f"   access_token 剩余: {expires_in // 60} 分钟")
        print(f"   refresh_token 剩余: {refresh_in // 86400} 天")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
