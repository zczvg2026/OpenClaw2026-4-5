#!/usr/bin/env python3
"""Analyze stocks with the Fenghuang return strategy."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple


EMOTION_SCORES = {
    "冰点": 0,
    "震荡": 65,
    "上升": 100,
    "退潮": 0,
}

PATTERN_SCORES = {
    "金凤凰": 100,
    "银凤凰": 85,
    "火凤凰": 70,
}

GRADE_SCORES = {
    "S": 100,
    "A": 85,
    "B": 70,
    "C": 55,
}

POSITION_BASE = {
    "S": 50.0,
    "A": 30.0,
    "B": 20.0,
    "C": 10.0,
}

TAKE_PROFIT_TEXT = {
    "heavy_volume_stall": "放量滞涨减仓",
    "upper_shadow": "高位上影减仓",
    "below_ma5": "跌破MA5止盈",
    "leader_breakdown": "龙头断板清仓",
    "emotion_retreat": "情绪退潮退出",
}

MODE_ALIASES = {
    "pre_market": "pre_market",
    "pre-market": "pre_market",
    "preopen": "pre_market",
    "auction": "pre_market",
    "竞价": "pre_market",
    "竞价预选": "pre_market",
    "盘前": "pre_market",
    "intraday": "intraday",
    "盘中": "intraday",
    "盘中扫描": "intraday",
    "post_market": "post_market",
    "post-market": "post_market",
    "postclose": "post_market",
    "after_close": "post_market",
    "盘后": "post_market",
    "盘后复盘": "post_market",
}

MODE_LABELS = {
    "pre_market": "竞价预选",
    "intraday": "盘中扫描",
    "post_market": "盘后复盘",
}

MODE_OUTPUT_TYPES = {
    "pre_market": "watchlist",
    "intraday": "buy_signal",
    "post_market": "review",
}

MODE_WEIGHTS = {
    "pre_market": {
        "emotion": 0.35,
        "sector": 0.25,
        "leader": 0.20,
        "pattern": 0.10,
        "grade": 0.10,
    },
    "intraday": {
        "emotion": 0.30,
        "sector": 0.25,
        "leader": 0.20,
        "pattern": 0.15,
        "grade": 0.10,
    },
    "post_market": {
        "emotion": 0.25,
        "sector": 0.25,
        "leader": 0.20,
        "pattern": 0.20,
        "grade": 0.10,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze stocks with the Fenghuang return strategy."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to JSON input. Use - to read from stdin.",
    )
    parser.add_argument(
        "--mode",
        help="Optional mode override. Supports pre_market, intraday, post_market and aliases.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    return parser.parse_args()


def load_json(path_arg: str) -> Dict[str, Any]:
    if path_arg == "-":
        return json.load(sys.stdin)
    with open(path_arg, "r", encoding="utf-8") as handle:
        return json.load(handle)


def safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return False


def time_key(value: Any) -> str:
    if not isinstance(value, str) or ":" not in value:
        return "99:99"
    return value.strip()


def normalize_mode(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    key = value.strip().lower()
    if not key:
        return None
    return MODE_ALIASES.get(key)


def infer_mode(market: Dict[str, Any], override: Optional[str] = None) -> str:
    explicit = normalize_mode(override)
    if explicit:
        return explicit

    explicit = normalize_mode(market.get("analysis_mode"))
    if explicit:
        return explicit

    snapshot_time = time_key(market.get("snapshot_time"))
    if snapshot_time != "99:99":
        if snapshot_time < "09:30":
            return "pre_market"
        if snapshot_time >= "15:00":
            return "post_market"
    return "intraday"


def infer_emotion(market: Dict[str, Any]) -> str:
    override = market.get("emotion_cycle")
    if override in EMOTION_SCORES:
        return override
    limit_up_count = safe_int(market.get("limit_up_count"))
    if truthy(market.get("high_mark_limit_down")):
        return "退潮"
    if limit_up_count < 20:
        return "冰点"
    if limit_up_count <= 50:
        return "震荡"
    return "上升"


def top_sectors(sectors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    valid = [sector for sector in sectors if truthy(sector.get("has_consecutive_board"))]
    return sorted(valid, key=lambda item: safe_int(item.get("limit_up_count")), reverse=True)[:3]


def build_leader_map(stocks: List[Dict[str, Any]]) -> Dict[str, str]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for stock in stocks:
        sector_name = str(stock.get("sector", "")).strip()
        if sector_name:
            grouped[sector_name].append(stock)

    leaders: Dict[str, str] = {}
    for sector_name, members in grouped.items():
        ordered = sorted(
            members,
            key=lambda item: (
                -safe_int(item.get("board_height"), safe_int(item.get("consecutive_limit_ups"))),
                time_key(item.get("first_limit_up_time")),
                -(safe_float(item.get("turnover_amount")) or 0.0),
            ),
        )
        symbol = str(ordered[0].get("symbol") or ordered[0].get("name") or "")
        if symbol:
            leaders[sector_name] = symbol
    return leaders


def first_board_half_level(stock: Dict[str, Any]) -> Optional[float]:
    explicit = safe_float(stock.get("first_board_half_level"))
    if explicit is not None:
        return explicit
    high = safe_float(stock.get("first_board_high"))
    low = safe_float(stock.get("first_board_low"))
    if high is None or low is None:
        return None
    return low + (high - low) / 2.0


def classify_pattern(stock: Dict[str, Any]) -> Tuple[Optional[str], List[str]]:
    reasons: List[str] = []
    pullback_low = safe_float(stock.get("pullback_low"))
    second_board_high = safe_float(stock.get("second_board_high"))
    first_board_high = safe_float(stock.get("first_board_high"))
    first_half = first_board_half_level(stock)

    if pullback_low is None:
        reasons.append("缺少 pullback_low")
        return None, reasons
    if second_board_high is not None and pullback_low >= second_board_high:
        return "金凤凰", reasons
    if first_board_high is not None and pullback_low >= first_board_high:
        return "银凤凰", reasons
    if first_half is not None and pullback_low >= first_half:
        return "火凤凰", reasons
    reasons.append("回调结构未达到火凤凰阈值")
    return None, reasons


def validate_pullback(stock: Dict[str, Any]) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    if truthy(stock.get("dropped_limit_after_second_board")):
        reasons.append("二板后跌停")
    if (safe_float(stock.get("max_daily_amplitude_pct")) or 0.0) > 15.0:
        reasons.append("单日振幅大于15%")
    if safe_int(stock.get("consecutive_long_bear_days")) >= 2:
        reasons.append("连续两日长阴")
    if (safe_float(stock.get("two_day_drop_pct")) or 0.0) > 15.0:
        reasons.append("两日跌幅大于15%")
    if truthy(stock.get("heavy_volume_down")):
        reasons.append("放量下跌")
    if truthy(stock.get("high_speed_up")):
        reasons.append("高位加速")
    return not reasons, reasons


def sector_component(sector_rank: Optional[int]) -> int:
    if sector_rank == 1:
        return 100
    if sector_rank == 2:
        return 85
    if sector_rank == 3:
        return 70
    return 0


def format_float(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(value, 3)


def stop_loss_levels(stock: Dict[str, Any]) -> Dict[str, Optional[float]]:
    level_3 = first_board_half_level(stock)
    return {
        "level_1_attack_candle_low": format_float(safe_float(stock.get("attack_candle_low"))),
        "level_2_first_board_close": format_float(safe_float(stock.get("first_board_close"))),
        "level_3_first_board_half": format_float(level_3),
    }


def primary_stop_loss(levels: Dict[str, Optional[float]]) -> Optional[float]:
    for key in (
        "level_1_attack_candle_low",
        "level_2_first_board_close",
        "level_3_first_board_half",
    ):
        if levels.get(key) is not None:
            return levels[key]
    return None


def take_profit_plan(stock: Dict[str, Any]) -> List[str]:
    flags = stock.get("take_profit_flags")
    if isinstance(flags, dict):
        active = [TAKE_PROFIT_TEXT[key] for key in TAKE_PROFIT_TEXT if truthy(flags.get(key))]
        if active:
            return active
    return list(TAKE_PROFIT_TEXT.values())


def planning_position(grade: Optional[str], is_leader: bool, emotion_cycle: str) -> float:
    base_position = POSITION_BASE.get(grade or "", 0.0)
    if not is_leader:
        base_position /= 2.0
    if emotion_cycle == "震荡":
        base_position /= 2.0
    return round(base_position, 2)


def score_total(
    emotion_score: int,
    board_score: int,
    leader_score: int,
    pattern_score: int,
    grade_score: int,
    mode: str,
) -> float:
    weights = MODE_WEIGHTS[mode]
    total = (
        emotion_score * weights["emotion"]
        + board_score * weights["sector"]
        + leader_score * weights["leader"]
        + pattern_score * weights["pattern"]
        + grade_score * weights["grade"]
    )
    return round(total, 2)


def shared_candidate_context(
    stock: Dict[str, Any],
    emotion_cycle: str,
    sector_ranks: Dict[str, int],
    leader_map: Dict[str, str],
) -> Dict[str, Any]:
    reasons: List[str] = []
    sector_name = str(stock.get("sector", "")).strip()
    symbol = str(stock.get("symbol") or stock.get("name") or "").strip()
    sector_rank = sector_ranks.get(sector_name)

    if sector_rank is None:
        reasons.append("所属板块不在Top3或缺少连板股")
    if safe_int(stock.get("consecutive_limit_ups")) < 2:
        reasons.append("未满足连续2个涨停前置条件")

    pullback_valid, pullback_reasons = validate_pullback(stock)
    if not pullback_valid:
        reasons.extend(pullback_reasons)

    phoenix_type, pattern_reasons = classify_pattern(stock)
    if phoenix_type is None:
        reasons.extend(pattern_reasons)

    is_leader = leader_map.get(sector_name) == symbol and bool(symbol)
    if emotion_cycle in {"冰点", "退潮"}:
        reasons.append(f"{emotion_cycle}期禁止主动开仓")

    return {
        "symbol": symbol,
        "name": stock.get("name"),
        "sector": sector_name,
        "sector_rank": sector_rank,
        "is_leader": is_leader,
        "phoenix_type": phoenix_type,
        "emotion_cycle": emotion_cycle,
        "base_reasons": reasons,
    }


def pre_market_grade(stock: Dict[str, Any], emotion_cycle: str) -> Tuple[Optional[str], List[str]]:
    reasons: List[str] = []
    open_pct = safe_float(stock.get("auction_open_pct"))
    volume_ratio = safe_float(stock.get("auction_volume_ratio"))
    locked = truthy(stock.get("preopen_locked"))
    leader_hint = truthy(stock.get("preopen_leader_strength"))

    if open_pct is None or volume_ratio is None:
        reasons.append("缺少竞价强度字段")
        return None, reasons
    if open_pct >= 5.0 and volume_ratio >= 2.0 and locked:
        return "S", reasons
    if open_pct >= 3.0 and volume_ratio >= 1.5:
        return "A", reasons
    if open_pct >= 1.0 and (locked or leader_hint):
        return "B", reasons
    if emotion_cycle == "上升" and open_pct > 0:
        return "C", reasons
    reasons.append("竞价强度不足")
    return None, reasons


def intraday_grade(stock: Dict[str, Any], emotion_cycle: str) -> Tuple[Optional[str], List[str]]:
    reasons: List[str] = []
    doubled_volume = truthy(stock.get("doubled_volume"))
    low_volume = truthy(stock.get("low_volume_consolidation"))
    breakout_confirmed = truthy(stock.get("intraday_breakout_confirmed")) or truthy(stock.get("breakout"))
    relock = truthy(stock.get("intraday_relock")) or truthy(stock.get("breakout"))
    breakout_adjustment = truthy(stock.get("breakout_adjustment_high"))
    ma10_supported = truthy(stock.get("ma10_supported"))
    bullish_engulfing = truthy(stock.get("bullish_engulfing"))
    rebound_signal = truthy(stock.get("rebound_signal"))

    if doubled_volume and low_volume and breakout_confirmed and relock:
        return "S", reasons
    if breakout_adjustment or breakout_confirmed:
        return "A", reasons
    if ma10_supported and bullish_engulfing:
        return "B", reasons
    if emotion_cycle == "上升" and rebound_signal:
        return "C", reasons
    reasons.append("未触发盘中有效买点")
    return None, reasons


def post_market_grade(stock: Dict[str, Any], emotion_cycle: str) -> Tuple[Optional[str], List[str]]:
    reasons: List[str] = []
    breakout = truthy(stock.get("breakout")) or truthy(stock.get("breakout_adjustment_high"))
    close_above_ma5 = truthy(stock.get("close_above_ma5"))
    close_near_high = truthy(stock.get("close_near_high"))
    heavy_volume_stall = truthy((stock.get("take_profit_flags") or {}).get("heavy_volume_stall"))
    ma10_supported = truthy(stock.get("ma10_supported"))
    bullish_engulfing = truthy(stock.get("bullish_engulfing"))
    rebound_signal = truthy(stock.get("rebound_signal"))

    if breakout and close_above_ma5 and close_near_high and not heavy_volume_stall:
        return "S", reasons
    if breakout and close_above_ma5:
        return "A", reasons
    if ma10_supported and bullish_engulfing:
        return "B", reasons
    if emotion_cycle == "上升" and rebound_signal:
        return "C", reasons
    reasons.append("未触发盘后复盘有效级别")
    return None, reasons


def build_common_result(
    shared: Dict[str, Any],
    mode: str,
    grade: Optional[str],
    extra_reasons: List[str],
) -> Dict[str, Any]:
    reasons = list(shared["base_reasons"]) + list(extra_reasons)
    if shared["emotion_cycle"] == "震荡" and grade not in {"S", "A"}:
        reasons.append("震荡期仅保留强信号")

    emotion_score = EMOTION_SCORES[shared["emotion_cycle"]]
    board_score = sector_component(shared["sector_rank"])
    leader_score = 100 if shared["is_leader"] else 50
    pattern_score = PATTERN_SCORES.get(shared["phoenix_type"] or "", 0)
    grade_score = GRADE_SCORES.get(grade or "", 0)
    score = score_total(
        emotion_score,
        board_score,
        leader_score,
        pattern_score,
        grade_score,
        mode,
    )
    eligible = not reasons and score > 0

    return {
        "symbol": shared["symbol"],
        "name": shared["name"],
        "sector": shared["sector"],
        "mode": mode,
        "mode_label": MODE_LABELS[mode],
        "output_type": MODE_OUTPUT_TYPES[mode],
        "emotion_cycle": shared["emotion_cycle"],
        "sector_rank": shared["sector_rank"],
        "is_leader": shared["is_leader"],
        "phoenix_type": shared["phoenix_type"],
        "setup_grade": grade,
        "score": score,
        "eligible": eligible,
        "reasons": reasons,
    }


def pre_market_reference_price(stock: Dict[str, Any]) -> Optional[float]:
    for key in ("auction_reference_price", "current_price", "breakout_price"):
        value = safe_float(stock.get(key))
        if value is not None:
            return format_float(value)
    return None


def intraday_entry_price(stock: Dict[str, Any]) -> Optional[float]:
    for key in ("breakout_price", "current_price", "adjustment_high"):
        value = safe_float(stock.get(key))
        if value is not None:
            return format_float(value)
    return None


def post_market_reference_price(stock: Dict[str, Any]) -> Optional[float]:
    for key in ("next_day_reference_price", "breakout_price", "current_price"):
        value = safe_float(stock.get(key))
        if value is not None:
            return format_float(value)
    return None


def evaluate_pre_market(
    stock: Dict[str, Any],
    shared: Dict[str, Any],
) -> Dict[str, Any]:
    grade, extra_reasons = pre_market_grade(stock, shared["emotion_cycle"])
    result = build_common_result(shared, "pre_market", grade, extra_reasons)
    planned_position = planning_position(grade, shared["is_leader"], shared["emotion_cycle"]) if result["eligible"] else 0.0

    if not result["eligible"]:
        priority = None
        action = "不加入观察名单"
    elif result["score"] >= 85:
        priority = "P1"
        action = "列入开盘重点盯盘"
    elif result["score"] >= 70:
        priority = "P2"
        action = "列入开盘观察"
    else:
        priority = "P3"
        action = "低优先级观察"

    result["suggested_position_pct"] = planned_position
    result["direct_entry_allowed"] = False
    result["mode_output"] = {
        "watchlist_priority": priority,
        "planned_action": action,
        "reference_price": pre_market_reference_price(stock),
    }
    return result


def evaluate_intraday(
    stock: Dict[str, Any],
    shared: Dict[str, Any],
) -> Dict[str, Any]:
    grade, extra_reasons = intraday_grade(stock, shared["emotion_cycle"])
    result = build_common_result(shared, "intraday", grade, extra_reasons)
    levels = stop_loss_levels(stock)
    planned_position = planning_position(grade, shared["is_leader"], shared["emotion_cycle"]) if result["eligible"] else 0.0
    direct_entry_allowed = result["eligible"]

    execution_style = None
    if direct_entry_allowed and grade == "S":
        execution_style = "突破后回封确认跟随"
    elif direct_entry_allowed and grade == "A":
        execution_style = "放量突破跟随"
    elif direct_entry_allowed and grade in {"B", "C"}:
        execution_style = "尾盘确认后评估进场"

    result["suggested_position_pct"] = planned_position
    result["direct_entry_allowed"] = direct_entry_allowed
    result["take_profit_plan"] = take_profit_plan(stock)
    result["mode_output"] = {
        "buy_signal": grade,
        "entry_price": intraday_entry_price(stock),
        "stop_loss": primary_stop_loss(levels),
        "stop_loss_levels": levels,
        "execution_style": execution_style,
    }
    return result


def post_market_hold_or_exit(stock: Dict[str, Any]) -> str:
    flags = stock.get("take_profit_flags") or {}
    if truthy(flags.get("leader_breakdown")) or truthy(flags.get("emotion_retreat")):
        return "优先退出"
    if truthy(flags.get("below_ma5")) or truthy(flags.get("upper_shadow")):
        return "减仓观察"
    return "持有并跟踪次日承接"


def evaluate_post_market(
    stock: Dict[str, Any],
    shared: Dict[str, Any],
) -> Dict[str, Any]:
    grade, extra_reasons = post_market_grade(stock, shared["emotion_cycle"])
    result = build_common_result(shared, "post_market", grade, extra_reasons)
    planned_position = planning_position(grade, shared["is_leader"], shared["emotion_cycle"]) if result["eligible"] else 0.0

    if not result["eligible"]:
        review_action = "仅记录，不进入次日计划"
        next_day_watchlist = None
    elif result["score"] >= 85:
        review_action = "加入次日重点观察池"
        next_day_watchlist = "核心观察"
    elif result["score"] >= 70:
        review_action = "加入次日备选池"
        next_day_watchlist = "备选观察"
    else:
        review_action = "保留复盘记录"
        next_day_watchlist = "低优先级观察"

    result["suggested_position_pct"] = planned_position
    result["direct_entry_allowed"] = False
    result["take_profit_plan"] = take_profit_plan(stock)
    result["mode_output"] = {
        "review_action": review_action,
        "next_day_watchlist": next_day_watchlist,
        "hold_or_exit": post_market_hold_or_exit(stock),
        "reference_price": post_market_reference_price(stock),
    }
    return result


def evaluate_stock(
    stock: Dict[str, Any],
    mode: str,
    emotion_cycle: str,
    sector_ranks: Dict[str, int],
    leader_map: Dict[str, str],
) -> Dict[str, Any]:
    shared = shared_candidate_context(stock, emotion_cycle, sector_ranks, leader_map)
    if mode == "pre_market":
        return evaluate_pre_market(stock, shared)
    if mode == "post_market":
        return evaluate_post_market(stock, shared)
    return evaluate_intraday(stock, shared)


def analyze(payload: Dict[str, Any], mode_override: Optional[str] = None) -> Dict[str, Any]:
    market = payload.get("market") or {}
    sectors = payload.get("sectors") or []
    stocks = payload.get("stocks") or []

    mode = infer_mode(market, mode_override)
    emotion_cycle = infer_emotion(market)
    selected_sectors = top_sectors(sectors)
    sector_ranks = {str(item.get("name", "")).strip(): index + 1 for index, item in enumerate(selected_sectors)}
    leader_map = build_leader_map(stocks)

    candidates = [
        evaluate_stock(stock, mode, emotion_cycle, sector_ranks, leader_map)
        for stock in stocks
    ]
    ordered = sorted(candidates, key=lambda item: (item["eligible"], item["score"]), reverse=True)
    eligible_count = sum(1 for item in ordered if item["eligible"])
    direct_entry_count = sum(1 for item in ordered if item.get("direct_entry_allowed"))

    return {
        "summary": {
            "mode": mode,
            "mode_label": MODE_LABELS[mode],
            "output_type": MODE_OUTPUT_TYPES[mode],
            "emotion_cycle": emotion_cycle,
            "market_limit_up_count": safe_int(market.get("limit_up_count")),
            "selected_sector_count": len(selected_sectors),
            "candidate_count": len(ordered),
            "eligible_count": eligible_count,
            "direct_entry_count": direct_entry_count,
        },
        "selected_sectors": selected_sectors,
        "candidates": ordered[:10],
    }


def render_markdown(result: Dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# 凤凰归巢策略分析结果",
        "",
        f"- 模式：{summary['mode']} ({summary['mode_label']})",
        f"- 输出类型：{summary['output_type']}",
        f"- 情绪周期：{summary['emotion_cycle']}",
        f"- 涨停家数：{summary['market_limit_up_count']}",
        f"- 入选板块数：{summary['selected_sector_count']}",
        f"- 候选股数：{summary['candidate_count']}",
        f"- 可用数量：{summary['eligible_count']}",
        f"- 可直接执行数量：{summary['direct_entry_count']}",
        "",
        "## 候选列表",
        "",
    ]

    if not result["candidates"]:
        lines.append("无候选数据。")
        return "\n".join(lines)

    for item in result["candidates"]:
        lines.extend(
            [
                f"### {item.get('name') or item.get('symbol')}",
                f"- 代码：{item.get('symbol')}",
                f"- 板块：{item.get('sector')}",
                f"- 模式：{item.get('mode')} ({item.get('mode_label')})",
                f"- 输出类型：{item.get('output_type')}",
                f"- 凤凰类型：{item.get('phoenix_type') or '无'}",
                f"- 级别：{item.get('setup_grade') or '无'}",
                f"- 综合评分：{item.get('score')}",
                f"- 计划仓位：{item.get('suggested_position_pct', 0.0)}%",
                f"- 可直接执行：{'是' if item.get('direct_entry_allowed') else '否'}",
            ]
        )
        mode_output = item.get("mode_output") or {}
        for key, value in mode_output.items():
            lines.append(f"- {key}：{value}")
        take_profit_plan = item.get("take_profit_plan")
        if take_profit_plan:
            lines.append(f"- 止盈计划：{'；'.join(take_profit_plan)}")
        reasons = item.get("reasons") or []
        if reasons:
            lines.append(f"- 风险/无效原因：{'；'.join(reasons)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    payload = load_json(args.input)
    result = analyze(payload, args.mode)

    if args.format == "markdown":
        sys.stdout.write(render_markdown(result))
    else:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
