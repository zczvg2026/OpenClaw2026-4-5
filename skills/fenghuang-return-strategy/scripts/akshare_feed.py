#!/opt/homebrew/bin/python3.13
"""
AKShare 数据管道 v2 — 加入 mootdx 历史K线+腾讯财经实时行情。

用法：
  python3 akshare_feed.py --stat-only                      # 只看统计
  python3 akshare_feed.py | python3 analyze_phoenix_strategy.py --input - --format markdown  # 全链路
"""

import argparse
import json
import sys
import warnings
from datetime import datetime, timedelta
from collections import defaultdict

warnings.filterwarnings("ignore")

VENV_SITE_PKG = "/Users/mac/.venv/aks/lib/python3.13/site-packages"
if VENV_SITE_PKG not in sys.path:
    sys.path.insert(0, VENV_SITE_PKG)

import akshare as ak
import pandas as pd
from mootdx.quotes import Quotes
import urllib.request


# ── 工具函数 ──────────────────────────────────────

def safe_str(val) -> str:
    if pd.isna(val): return ""
    return str(val).strip()

def safe_float(val) -> float:
    try:
        v = float(val)
        return 0.0 if pd.isna(v) else v
    except: return 0.0

def safe_int(val) -> int:
    try:
        v = int(float(val))
        return 0 if pd.isna(v) else v
    except: return 0

def truthy(val) -> bool:
    if isinstance(val, bool): return val
    if isinstance(val, (int, float)): return val != 0
    if isinstance(val, str): return val.strip().lower() in ("1", "true", "yes", "y")
    return False

def get_today_str() -> str:
    return datetime.now().strftime("%Y%m%d")

def get_now_time() -> str:
    return datetime.now().strftime("%H:%M")

def infer_mode_from_time() -> str:
    t = get_now_time()
    if t < "09:30": return "pre_market"
    if t >= "15:00": return "post_market"
    return "intraday"

def get_prefix(code: str) -> str:
    if code.startswith(("6", "9")): return "sh"
    if code.startswith("8"): return "bj"
    return "sz"


# ── Layer 1: mootdx K线 ───────────────────────────

_client = None
def get_mootdx():
    global _client
    if _client is None:
        _client = Quotes.factory(market='std')
    return _client

def fetch_klines(symbol: str, days: int = 60) -> pd.DataFrame:
    """获取日K线"""
    try:
        return get_mootdx().bars(symbol=symbol, category=4, offset=days)
    except Exception as e:
        print(f"  ⚠ mootdx K线失败 {symbol}: {e}", file=sys.stderr)
        return pd.DataFrame()


# ── Layer 1: 腾讯财经实时行情 ─────────────────────

def tencent_quote(codes: list) -> dict:
    result = {}
    chunk_size = 50
    for i in range(0, len(codes), chunk_size):
        chunk = codes[i:i+chunk_size]
        prefixed = [f"{get_prefix(c)}{c}" for c in chunk]
        url = "https://qt.gtimg.cn/q=" + ",".join(prefixed)
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            data = resp.read().decode("gbk")
            for line in data.strip().split(";"):
                if not line.strip() or "=" not in line or '"' not in line:
                    continue
                key = line.split("=")[0].split("_")[-1]
                vals = line.split('"')[1].split("~")
                if len(vals) < 53: continue
                code = key[2:]
                result[code] = {
                    "price": float(vals[3]),
                    "last_close": float(vals[4]),
                    "high": float(vals[33]),
                    "low": float(vals[34]),
                    "amount_wan": float(vals[37]),
                    "turnover_pct": float(vals[38]),
                    "pe_ttm": float(vals[39]),
                    "mcap_yi": float(vals[44]),
                    "pb": float(vals[46]),
                    "limit_up": float(vals[47]),
                    "limit_down": float(vals[48]),
                }
        except Exception as e:
            print(f"  ⚠ 腾讯行情失败: {e}", file=sys.stderr)
    return result


# ── 数据获取 ──────────────────────────────────────

def fetch_limit_up_pool(date_str: str) -> pd.DataFrame:
    df = ak.stock_zt_pool_em(date=date_str)
    if df.empty:
        return df
    # 统一列名
    df = df.rename(columns={
        "代码": "symbol", "名称": "name", "涨跌幅": "pct_chg",
        "最新价": "price", "成交额": "amount", "换手率": "turnover",
        "首次封板时间": "first_seal_time", "连板数": "board_count",
        "所属行业": "sector", "涨停统计": "board_stat",
    })
    return df

def fetch_down_limit_pool(date_str: str) -> pd.DataFrame:
    try:
        df = ak.stock_zt_pool_dtgc_em(date=date_str)
        if not df.empty:
            df = df.rename(columns={
                "代码": "symbol", "名称": "name", "涨跌幅": "pct_chg",
                "最新价": "price", "成交额": "amount", "所属行业": "sector",
            })
        return df
    except: return pd.DataFrame()


# ── K线回补：检测涨停日 + 补回调结构 ──────────────

def detect_limit_up_days(klines: pd.DataFrame) -> list:
    """从K线中检测涨停日，返回 [(datetime, open, high, low, close), ...]"""
    if klines.empty:
        return []
    results = []
    for _, row in klines.iterrows():
        o, h, l, c = row["open"], row["high"], row["low"], row["close"]
        # 涨停条件：close == high 且涨幅接近10%
        if h > 0 and abs(c - h) / h < 0.001:
            dt = row["datetime"]
            if isinstance(dt, pd.Timestamp):
                dt = dt.strftime("%Y-%m-%d")
            results.append((str(dt), o, h, l, c))
    return results

def enrich_with_klines(zt_df: pd.DataFrame) -> pd.DataFrame:
    """为连板股补K线数据字段：first_board_high/low/close, second_board_high, pullback_low等"""
    enriched = []
    board_codes = zt_df[zt_df["board_count"] >= 2]["symbol"].tolist()

    if not board_codes:
        print("  ℹ 没有连板股，跳过K线回补", file=sys.stderr)
        return zt_df

    print(f"  📊 K线回补: {len(board_codes)} 只连板股", file=sys.stderr)

    for _, row in zt_df.iterrows():
        r = row.to_dict()
        code = safe_str(r.get("symbol", ""))
        board = safe_int(r.get("board_count"))

        if code in board_codes and board >= 2:
            klines = fetch_klines(code)
            if not klines.empty:
                lu_days = detect_limit_up_days(klines)
                if len(lu_days) >= 2:
                    # 最近2个涨停日（倒序）
                    d2, o2, h2, l2, c2 = lu_days[-1]  # 最晚 = second board
                    d1, o1, h1, l1, c1 = lu_days[-2]  # 前一个 = first board
                    r["first_board_high"] = h1
                    r["first_board_low"] = l1
                    r["first_board_close"] = c1
                    r["second_board_high"] = h2
                    # pullback_low: 两涨停日之间的最低点
                    between = klines[klines["datetime"].between(d1, d2)]
                    if len(between) > 1:
                        r["pullback_low"] = between["low"].min()
                    else:
                        r["pullback_low"] = l1  # 连续板无间隔
                    # 回调验证
                    if safe_int(r.get("consecutive_long_bear_days")):
                        pass  # 留空，后续可补
                    if len(lu_days) >= 3:
                        # 有三波涨停 → 已有回调结构验证
                        pass
                elif len(lu_days) == 1:
                    # 只有今天涨停，历史数据不够
                    pass
            else:
                print(f"    ⚠ {code} K线数据为空", file=sys.stderr)

        enriched.append(r)

    return pd.DataFrame(enriched)


# ── 构建输出 ──────────────────────────────────────

def build_market_data(zt_df: pd.DataFrame, dt_df: pd.DataFrame) -> dict:
    limit_up_count = len(zt_df)
    high_mark_limit_down = False
    if not dt_df.empty and len(dt_df) > 5:
        high_mark_limit_down = True
    return {
        "analysis_mode": infer_mode_from_time(),
        "snapshot_time": get_now_time(),
        "limit_up_count": limit_up_count,
        "high_mark_limit_down": high_mark_limit_down,
    }

def build_sectors(zt_df: pd.DataFrame) -> list:
    if zt_df.empty or "sector" not in zt_df.columns:
        return []
    sectors = []
    for sector, group in zt_df.groupby("sector"):
        name = safe_str(sector)
        if not name: continue
        max_board = safe_int(group["board_count"].max())
        sectors.append({
            "name": name,
            "limit_up_count": len(group),
            "has_consecutive_board": max_board >= 2,
        })
    sectors.sort(key=lambda x: x["limit_up_count"], reverse=True)
    return sectors

def build_stocks(zt_df: pd.DataFrame) -> list:
    stocks = []
    for _, row in zt_df.iterrows():
        symbol = safe_str(row.get("symbol", ""))
        name = safe_str(row.get("name", ""))
        sector = safe_str(row.get("sector", ""))
        board_height = safe_int(row.get("board_count"))
        first_time = safe_str(row.get("first_seal_time", ""))
        turnover = safe_float(row.get("amount"))
        price = safe_float(row.get("price"))

        stock = {
            "symbol": symbol, "name": name, "sector": sector,
            "consecutive_limit_ups": board_height, "board_height": board_height,
            "first_limit_up_time": first_time, "turnover_amount": turnover,
            "current_price": price,
        }

        # K线回补字段（由 enrich_with_klines 填充）
        for k in ["first_board_high", "first_board_low", "first_board_close",
                   "second_board_high", "pullback_low"]:
            val = row.get(k)
            stock[k] = val if pd.notna(val) else None

        # 占位字段（策略需要但当前数据不包含的）
        for k in ["auction_open_pct", "auction_volume_ratio", "preopen_locked",
                   "intraday_breakout_confirmed", "intraday_relock",
                   "close_above_ma5", "close_near_high",
                   "dropped_limit_after_second_board", "max_daily_amplitude_pct",
                   "consecutive_long_bear_days", "two_day_drop_pct",
                   "heavy_volume_down", "high_speed_up",
                   "doubled_volume", "low_volume_consolidation",
                   "breakout", "breakout_adjustment_high", "ma10_supported",
                   "bullish_engulfing", "rebound_signal",
                   "breakout_price", "attack_candle_low"]:
            if k not in stock:
                stock[k] = None

        stocks.append(stock)
    return stocks


# ── 主流程 ───────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AKShare 数据管道 v2")
    parser.add_argument("--mode", choices=["pre_market", "intraday", "post_market"])
    parser.add_argument("--date", help="YYYYMMDD")
    parser.add_argument("--stat-only", action="store_true")
    args = parser.parse_args()

    date_str = args.date or get_today_str()
    print(f"📡 获取数据: {date_str} {get_now_time()}", file=sys.stderr)

    zt_raw = fetch_limit_up_pool(date_str)
    dt_raw = fetch_down_limit_pool(date_str)

    print(f"📈 涨停: {len(zt_raw)} 只", file=sys.stderr)
    print(f"📉 跌停: {len(dt_raw)} 只", file=sys.stderr)

    if zt_raw.empty:
        print("❌ 无涨停数据", file=sys.stderr)
        json.dump({"market": {}, "sectors": [], "stocks": []}, sys.stdout)
        return

    # K线回补：为连板股补充回调结构
    zt_enriched = enrich_with_klines(zt_raw)

    if args.stat_only:
        sectors = build_sectors(zt_enriched)
        print("\n🔥 板块涨停Top10:", file=sys.stderr)
        for i, s in enumerate(sectors[:10], 1):
            board_str = ""
            if s["has_consecutive_board"]:
                # 看看这个板块的龙头是哪个
                sector_stocks = zt_enriched[zt_enriched["sector"] == s["name"]]
                max_board = sector_stocks["board_count"].max()
                top_stock = sector_stocks.sort_values("board_count", ascending=False).iloc[0]
                board_str = f" 龙头:{top_stock['name']}({int(max_board)}板)"
            print(f"  {i}. {s['name']}: {s['limit_up_count']}只涨停 {board_str}", file=sys.stderr)
        return

    result = {
        "market": build_market_data(zt_enriched, dt_raw),
        "sectors": build_sectors(zt_enriched),
        "stocks": build_stocks(zt_enriched),
    }
    if args.mode:
        result["market"]["analysis_mode"] = args.mode

    print(f"\n⬇️ 模式: {result['market']['analysis_mode']}", file=sys.stderr)
    print(f"✅ 输出: {len(result['stocks'])} 只候选股", file=sys.stderr)

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
