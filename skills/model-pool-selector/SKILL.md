---
name: model-pool-selector
description: |
  模型池自动选择器。根据任务类型自动选择合适的模型，并处理模型失败时的自动fallback。
  当用户发起新任务、或需要根据任务复杂度选择模型时使用此技能。
  也会在模型调用失败（rate limit、token耗尽）时自动切换备用模型。
homepage: https://github.com/openclaw/openclaw
metadata:
  {
    "openclaw":
      {
        "emoji": "🎯",
        "requires": {},
      },
  }
---

# model-pool-selector

根据任务类型自动选择合适的模型，并处理失败时的自动切换。

## 模型池定义

### 高速池（Fast Pool）
任务：简单日常会话、简单查询、快速响应
主模型：`step-2-mini`
备用：`step-1-8k`、`minimax-portal/MiniMax-M2.5-Lightning`

### 智能池（Smart Pool）
任务：大型复杂任务、高强度推理、代码生成、深度分析
主模型：`step-1-256k`
备用：`step-3`、`minimax-portal/MiniMax-M2.5`

### 文本池（Text Pool）
任务：文本处理、长文分析、文档总结、多轮对话
主模型：`step-1-32k`
备用：`step-3.5-flash`

## 任务类型判断

根据用户输入的关键词判断：

| 关键词 | 池 |
|--------|-----|
| 写代码、编程、debug、修复 | 智能池 |
| 分析、深度思考、为什么、原理 | 智能池 |
| 总结、摘要、翻译、润色 | 文本池 |
| 列表、查询、天气、时间 | 高速池 |
| 简单问题、问候、日常对话 | 高速池 |

## 使用方式

### 手动选择

```
# 指定使用某模型池
@agent 使用智能池分析这段代码
@agent 用文本池总结这个文档
```

### 自动选择

当用户发起新任务时，根据任务内容自动判断并选择合适的模型。

## 故障处理

当主模型失败时（rate limit、quota exhausted），自动切换到备用模型：

1. 检测到错误码：`20002`（rate limit）、`110037`（apikey过期）等
2. 自动切换到备用模型
3. 继续执行任务

## 配置

当前可用模型（已配置）：

```json
{
  "stepfun": ["step-1-8k", "step-1-32k", "step-1-256k", "step-2-mini", "step-3", "step-3.5-flash"],
  "minimax-portal": ["MiniMax-M2.5", "MiniMax-M2.5-Lightning"]
}
```
