/**
 * config_schema.ts
 * 用 Zod 验证 heartbeat-state 和 cron-jobs 的 schema
 * zod 来自 openclaw 的 bundled node_modules
 */

// Node.js CJS 环境
const { z } = require('/opt/homebrew/lib/node_modules/openclaw/node_modules/zod')

// ── HeartbeatState ───────────────────────────────────────────────────────────

const HeartbeatStateSchema = z.object({
  lastChecks: z.object({
    email: z.number().nullable(),
    calendar: z.number().nullable(),
  }),
  stateFileMtime: z.number().nullable(),
  note: z.string(),
})

// ── CronTask ─────────────────────────────────────────────────────────────────

const CronTaskSchema = z.object({
  id: z.string(),
  jitterSecondsMax: z.number().min(0).max(3600).default(0),
  lastFiredAt: z.number().nullable().optional(),
  missedRuns: z.number().min(0).default(0),
  recurring: z.boolean().optional(),
  permanent: z.boolean().optional(),
  title: z.string(),
  status: z.string(),
  schedule_type: z.string().nullable(),
  interval: z.string().nullable(),
  time_of_day: z.string().nullable(),
  days_of_week: z.array(z.string()),
  day_of_month: z.number().nullable(),
  timezone: z.string(),
  start_date: z.string().nullable(),
  end_date: z.string().nullable(),
  last_run_at: z.string().nullable(),
  next_run_at: z.string(),
  notes: z.string(),
  tags: z.array(z.string()),
  created_at: z.string(),
  updated_at: z.string(),
})

// ── Validators ───────────────────────────────────────────────────────────────

function validateHeartbeatState(raw) {
  return HeartbeatStateSchema.safeParse(raw)
}

function validateCronJobs(raw) {
  return z.record(z.string(), CronTaskSchema).safeParse(raw)
}

// CLI test
if (require.main === module) {
  const rawHb = { lastChecks: { email: null, calendar: null }, stateFileMtime: null, note: 'test' }
  const r1 = validateHeartbeatState(rawHb)
  console.log('HeartbeatState valid:', r1.success)
  if (!r1.success) console.error('Error:', r1.error.message)
  
  const jobs = require('./memory/cron/jobs.json')
  const r2 = validateCronJobs(jobs.jobs)
  console.log('CronJobs valid:', r2.success)
  if (!r2.success) console.error('Error:', r2.error.message)
}

module.exports = { validateHeartbeatState, validateCronJobs, HeartbeatStateSchema, CronTaskSchema }
