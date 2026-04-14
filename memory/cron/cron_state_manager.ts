/**
 * cron_state_manager.ts
 * 独立的 Cron 状态管理脚本，不依赖 OpenClaw 内部 API
 * 用法：npx tsx memory/cron/cron_state_manager.ts <command>
 */

import { promises as fs } from 'fs'
import { join } from 'path'

const JOBS_FILE = '/Users/mac/.openclaw/workspace/memory/cron/jobs.json'
const FEISHU_CHANNEL = process.env.FEISHU_WEBHOOK_URL ?? ''

export interface CronJob {
  id: string
  title: string
  status: string
  schedule_type: string | null
  interval: string | null
  time_of_day: string | null
  days_of_week: string[]
  day_of_month: number | null
  timezone: string
  start_date: string | null
  end_date: string | null
  last_run_at: string | null
  next_run_at: string
  lastFiredAt: number | null
  jitterSecondsMax: number
  missedRuns: number
  notes: string
  tags: string[]
  created_at: string
  updated_at: string
}

interface JobsFile {
  metadata: Record<string, unknown>
  jobs: Record<string, CronJob>
}

// ── read/write ──────────────────────────────────────────────────────────────

export async function readJobs(): Promise<JobsFile> {
  const raw = await fs.readFile(JOBS_FILE, 'utf-8')
  return JSON.parse(raw) as JobsFile
}

export async function writeJobs(data: JobsFile): Promise<void> {
  await fs.writeFile(JOBS_FILE, JSON.stringify(data, null, 2), 'utf-8')
}

// ── jitter ──────────────────────────────────────────────────────────────────

/**
 * 计算加 jitter 后的下次执行时间
 * actualFireTime = scheduledTime + random(0, jitterSecondsMax)
 */
export function computeNextRunWithJitter(job: CronJob): Date {
  const scheduledMs = new Date(job.next_run_at).getTime()
  const jitterMs = Math.floor(Math.random() * (job.jitterSecondsMax ?? 0)) * 1000
  return new Date(scheduledMs + jitterMs)
}

// ── missed runs ──────────────────────────────────────────────────────────────

/**
 * 检查是否错过执行时间，若是则补跑（发飞书通知）
 */
export async function checkAndFireMissed(job: CronJob): Promise<boolean> {
  if (job.status !== 'active') return false

  const now = Date.now()
  const scheduledMs = new Date(job.next_run_at).getTime()
  const jitteredMs = scheduledMs + Math.floor(Math.random() * (job.jitterSecondsMax ?? 0)) * 1000

  if (now < jitteredMs) return false

  // 错过了，补跑
  if (FEISHU_CHANNEL) {
    try {
      await fetch(FEISHU_CHANNEL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          msg_type: 'text',
          content: {
            text: `🦀【Cron 漏跑，已补跑】\n任务：${job.title}（${job.id}）\n计划时间：${job.next_run_at}\n当前时间：${new Date().toISOString()}`,
          },
        }),
      })
    } catch (err) {
      console.error('[cron_state_manager] 飞书通知失败:', err)
    }
  }

  // 增加 missedRuns 计数（将在 updateNextRun 中重置）
  return true
}

// ── lastFiredAt ──────────────────────────────────────────────────────────────

/**
 * 执行后更新 lastFiredAt 为当前时间（毫秒）
 */
export async function updateLastFired(jobId: string): Promise<void> {
  const data = await readJobs()
  const job = data.jobs[jobId]
  if (!job) {
    console.warn(`[cron_state_manager] job not found: ${jobId}`)
    return
  }
  job.lastFiredAt = Date.now()
  job.missedRuns = 0 // 补跑完成后重置
  job.updated_at = new Date().toISOString()
  await writeJobs(data)
}

// ── computeNextRun ───────────────────────────────────────────────────────────

/**
 * 根据 schedule_type 计算下一个计划时间（不含 jitter）
 * 调用前确保 job 的 last_run_at 已更新
 */
export function computeNextSchedule(job: CronJob): Date {
  const now = new Date()
  const [hour, minute] = (job.time_of_day ?? '00:00').split(':').map(Number)

  if (job.schedule_type === 'daily') {
    const next = new Date(now)
    next.setHours(hour, minute, 0, 0)
    if (next.getTime() <= now.getTime()) {
      next.setDate(next.getDate() + 1)
    }
    return next
  }

  // fallback: 加一天
  const next = new Date(now.getTime() + 86_400_000)
  next.setHours(hour, minute, 0, 0)
  return next
}

// ── CLI ─────────────────────────────────────────────────────────────────────

async function main() {
  const cmd = process.argv[2]

  if (cmd === 'read') {
    const data = await readJobs()
    console.log(JSON.stringify(data, null, 2))
    return
  }

  if (cmd === 'update-last-fired') {
    const jobId = process.argv[3]
    if (!jobId) { console.error('Usage: update-last-fired <jobId>'); process.exit(1) }
    await updateLastFired(jobId)
    console.log(`✅ lastFiredAt updated for ${jobId}`)
    return
  }

  if (cmd === 'test-jitter') {
    const jobId = process.argv[3] ?? 'JOB-18BE'
    const data = await readJobs()
    const job = data.jobs[jobId]
    if (!job) { console.error(`job not found: ${jobId}`); process.exit(1) }
    // 模拟10次jitter
    for (let i = 0; i < 10; i++) {
      const jittered = computeNextRunWithJitter(job)
      console.log(`  run ${i + 1}: ${jittered.toISOString()}`)
    }
    return
  }

  console.log('Commands: read | update-last-fired <jobId> | test-jitter [jobId]')
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
