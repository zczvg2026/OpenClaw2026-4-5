# Cron Jitter 配置

## 为什么需要 Jitter？

- 防止 22:30 全网 10000 台设备同时触发 → 服务器被打爆
- 每个 cron 任务在计划时间上随机偏移 0~N 分钟

## OpenClaw 抖动实现

- 在 `memory/cron/jobs.json` 的每条 job 里配置 `jitterSecondsMax`
- 推荐值：
  - 每日任务（22:30）：`jitterSecondsMax: 300`（0~5分钟）
  - 每日备份（03:00）：`jitterSecondsMax: 600`（0~10分钟）
  - 每周任务：`jitterSecondsMax: 1800`（0~30分钟）
  - 一次性任务：不加 jitter（`jitterSecondsMax: 0`）

## 算法

```
actualFireTime = scheduledTime + random(0, jitterSecondsMax)
```

## 实现（cron_state_manager.ts）

```typescript
function computeNextRunWithJitter(job: CronJob): Date {
  const scheduled = new Date(job.next_run_at).getTime()
  const jitter = Math.floor(Math.random() * (job.jitterSecondsMax ?? 0)) * 1000
  return new Date(scheduled + jitter)
}
```
