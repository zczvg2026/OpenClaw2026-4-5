# 输入结构

脚本输入为一个 JSON 文件。顶层结构如下：

```json
{
  "market": {
    "analysis_mode": "intraday",
    "snapshot_time": "10:26",
    "limit_up_count": 68,
    "high_mark_limit_down": false
  },
  "sectors": [
    {
      "name": "机器人",
      "limit_up_count": 8,
      "has_consecutive_board": true
    }
  ],
  "stocks": [
    {
      "symbol": "000001",
      "name": "示例股份",
      "sector": "机器人",
      "consecutive_limit_ups": 2,
      "board_height": 2,
      "first_limit_up_time": "09:31",
      "turnover_amount": 1800000000,
      "auction_open_pct": 4.8,
      "auction_volume_ratio": 2.1,
      "preopen_locked": true,
      "intraday_breakout_confirmed": true,
      "intraday_relock": true,
      "close_above_ma5": true,
      "close_near_high": true,
      "dropped_limit_after_second_board": false,
      "max_daily_amplitude_pct": 8.5,
      "consecutive_long_bear_days": 0,
      "two_day_drop_pct": 6.2,
      "heavy_volume_down": false,
      "high_speed_up": false,
      "first_board_high": 12.8,
      "first_board_low": 11.6,
      "first_board_close": 12.5,
      "second_board_high": 13.9,
      "pullback_low": 14.1,
      "doubled_volume": true,
      "low_volume_consolidation": true,
      "breakout": true,
      "breakout_adjustment_high": true,
      "ma10_supported": true,
      "bullish_engulfing": false,
      "rebound_signal": true,
      "current_price": 14.35,
      "breakout_price": 14.32,
      "attack_candle_low": 13.88,
      "take_profit_flags": {
        "heavy_volume_stall": false,
        "upper_shadow": false,
        "below_ma5": false,
        "leader_breakdown": false,
        "emotion_retreat": false
      }
    }
  ]
}
```

## 顶层字段

- `market.analysis_mode`: 可选。支持 `pre_market`、`intraday`、`post_market`，也兼容旧别名
- `market.snapshot_time`: 可选。`HH:MM`；未显式给模式时可据此推断
- `market.limit_up_count`: 当日涨停家数
- `market.high_mark_limit_down`: 是否存在高标跌停
- `sectors`: 板块列表
- `stocks`: 候选股票列表

## 板块字段

- `name`: 板块名称
- `limit_up_count`: 板块涨停家数
- `has_consecutive_board`: 是否存在连板股

## 个股字段

- `symbol`: 股票代码
- `name`: 股票名称
- `sector`: 所属板块
- `consecutive_limit_ups`: 连续涨停数
- `board_height`: 连板高度
- `first_limit_up_time`: 首次封板时间，`HH:MM`
- `turnover_amount`: 成交额
- `auction_open_pct`: 竞价涨幅
- `auction_volume_ratio`: 竞价量比
- `preopen_locked`: 竞价封单是否稳定
- `intraday_breakout_confirmed`: 盘中是否完成突破确认
- `intraday_relock`: 盘中是否回封或再度走强
- `close_above_ma5`: 收盘是否站上 MA5
- `close_near_high`: 收盘是否接近全天高位
- `dropped_limit_after_second_board`: 二板后是否跌停
- `max_daily_amplitude_pct`: 回调阶段单日最大振幅
- `consecutive_long_bear_days`: 连续长阴天数
- `two_day_drop_pct`: 两日累计跌幅
- `heavy_volume_down`: 是否放量下跌
- `high_speed_up`: 是否高位加速
- `first_board_high`: 首板高点
- `first_board_low`: 首板低点
- `first_board_close`: 首板收盘价
- `second_board_high`: 二板高点
- `pullback_low`: 回调低点
- `doubled_volume`: 是否倍量柱
- `low_volume_consolidation`: 是否缩量整理
- `breakout`: 是否放量突破
- `breakout_adjustment_high`: 是否突破调整高点
- `ma10_supported`: 是否获得 MA10 支撑
- `bullish_engulfing`: 是否阳线反包
- `rebound_signal`: 是否存在反弹触发
- `current_price`: 当前价
- `breakout_price`: 突破价
- `attack_candle_low`: 上攻 K 线低点
- `take_profit_flags`: 动态止盈触发状态

## 输出说明

脚本输出包含：

- `summary`: 模式、输出类型、市场情绪、板块数量、候选数量、可用数量
- `candidates`: 每只股票的共享上下文、模式专属输出、风险与建议

### pre_market 输出

- `output_type`: `watchlist`
- `mode_output.watchlist_priority`
- `mode_output.planned_action`
- `mode_output.reference_price`

### intraday 输出

- `output_type`: `buy_signal`
- `mode_output.buy_signal`
- `mode_output.entry_price`
- `mode_output.stop_loss`
- `mode_output.execution_style`

### post_market 输出

- `output_type`: `review`
- `mode_output.review_action`
- `mode_output.next_day_watchlist`
- `mode_output.hold_or_exit`

如果字段缺失，脚本会在 `reasons` 中明确指出。
