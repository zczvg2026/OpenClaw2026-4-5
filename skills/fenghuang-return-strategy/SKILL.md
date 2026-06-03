---
name: fenghuang-return-strategy
description: 基于二连板洗盘回归模型，对A股短线题材股执行凤凰归巢策略筛选、情绪评估、板块排序、龙头识别、形态分类、买卖点判断、仓位分配与风控止盈。用于用户提供市场情绪、板块热度、涨停数据、个股结构化JSON或表格时，按 pre_market、intraday、post_market 三个独立规则域输出观察名单、盘中买点或盘后复盘结论。
---

# 凤凰归巢策略

## 目标

将“情绪 > 板块 > 龙头 > 形态 > 买点”的优先级固化为可重复执行的短线交易流程，并按时间维度拆成三个独立规则域。

在收到结构化市场数据时，优先调用 `scripts/analyze_phoenix_strategy.py` 生成候选结果，再结合上下文补充解释。

## 执行流程

1. 根据 `market.analysis_mode`、`market.snapshot_time` 或命令行参数识别模式。
2. 先执行共享上下文：
   - 情绪判断
   - 板块 Top3
   - 龙头识别
   - 二连板前置过滤
   - 洗盘结构与凤凰模型识别
3. 再进入独立规则域：
   - `pre_market` 只输出观察名单
   - `intraday` 只输出盘中买点与执行参数
   - `post_market` 只输出复盘结论与次日计划

## 工作规则

- 在存在结构化 JSON 数据时，运行：

```bash
python3 scripts/analyze_phoenix_strategy.py --input /path/to/input.json --format markdown
python3 scripts/analyze_phoenix_strategy.py --input /path/to/input.json --mode intraday --format json
python3 scripts/analyze_phoenix_strategy.py --input /path/to/input.json --mode pre_market --format json
```

- 在只有自然语言、截图或表格时，先整理成 [references/input-schema.md](references/input-schema.md) 定义的结构，再运行脚本。
- 允许三种模式：
  - `pre_market`：只做竞价/盘前观察名单，不输出买点。
  - `intraday`：只做盘中买点与执行，不输出复盘结论。
  - `post_market`：只做盘后复盘与次日计划，不输出即时买点。
- 在市场处于“冰点”或“退潮”时，不给出主动开仓建议；可以保留复盘或观察结论，但必须明确标注不可直接执行。
- 在“震荡”期，只保留强信号，优先 S/A 级买点。
- 在非龙头个股上，将基础仓位减半。
- 在字段缺失时，不得臆造涨停数、连板高度、均线支撑或突破条件；明确返回缺失项。

## 输出要求

输出中至少包含以下字段：

- 股票名称
- 股票代码
- 板块
- 情绪周期
- 凤凰类型
- 模式类型
- 建议仓位
- 执行动作
- 模式专属输出
- 止盈策略
- 综合评分
- 无效原因或风险标记

## 资源

- 读取 [references/strategy-rules.md](references/strategy-rules.md) 获取完整阈值、优先级和评分口径。
- 读取 [references/input-schema.md](references/input-schema.md) 获取脚本输入结构。
- 使用 `scripts/analyze_phoenix_strategy.py` 对候选池做自动筛选和评分。
