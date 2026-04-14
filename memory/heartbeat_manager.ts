/**
 * heartbeat_manager.ts
 * 心跳状态管理：基于文件 mtime 做 TTL 判断
 * 若 mtime 不work（某些网络文件系统），fallback 到内容里的时间戳
 */

import { promises as fs } from 'fs'
import { stat } from 'fs/promises'

const STATE_FILE = '/Users/mac/.openclaw/workspace/memory/heartbeat-state.json'

// ── init ─────────────────────────────────────────────────────────────────────

export async function init(): Promise<void> {
  try {
    await stat(STATE_FILE)
  } catch {
    const initial = {
      lastChecks: { email: null, calendar: null },
      stateFileMtime: Date.now(),
      note: 'lastHeartbeat 不再存时间戳，改为用 stateFileMtime 判断新鲜度。gateway 每次心跳时 touch() 即可。',
    }
    await fs.writeFile(STATE_FILE, JSON.stringify(initial, null, 2), 'utf-8')
  }
}

// ── touch ───────────────────────────────────────────────────────────────────

/**
 * 更新 stateFileMtime 到当前时间
 */
export async function touch(): Promise<number> {
  const now = Date.now()
  const raw = await fs.readFile(STATE_FILE, 'utf-8')
  const state = JSON.parse(raw)
  state.stateFileMtime = now
  await fs.writeFile(STATE_FILE, JSON.stringify(state, null, 2), 'utf-8')
  return now
}

// ── isFresh ──────────────────────────────────────────────────────────────────

export async function isFresh(maxAgeMs: number): Promise<boolean> {
  const ageMs = await getAgeMs()
  return ageMs !== null && ageMs <= maxAgeMs
}

// ── getAgeMs ─────────────────────────────────────────────────────────────────

export async function getAgeMs(): Promise<number | null> {
  try {
    const raw = await fs.readFile(STATE_FILE, 'utf-8')
    const state = JSON.parse(raw)
    const mtime = state.stateFileMtime
    if (typeof mtime !== 'number') return null
    return Date.now() - mtime
  } catch {
    return null
  }
}

// ── readState ───────────────────────────────────────────────────────────────

export async function readState(): Promise<Record<string, unknown>> {
  const raw = await fs.readFile(STATE_FILE, 'utf-8')
  return JSON.parse(raw)
}

// ── CLI ─────────────────────────────────────────────────────────────────────

async function main() {
  const cmd = process.argv[2]

  if (cmd === 'init') {
    await init()
    console.log('✅ heartbeat state initialized')
    return
  }

  if (cmd === 'touch') {
    const now = await touch()
    console.log(`✅ touched at ${now}`)
    return
  }

  if (cmd === 'fresh') {
    const maxAgeMs = parseInt(process.argv[3] ?? '300000', 10)
    const fresh = await isFresh(maxAgeMs)
    const age = await getAgeMs()
    console.log(`fresh: ${fresh}  ageMs: ${age}`)
    return
  }

  if (cmd === 'age') {
    const age = await getAgeMs()
    console.log(`ageMs: ${age}`)
    return
  }

  if (cmd === 'state') {
    const s = await readState()
    console.log(JSON.stringify(s, null, 2))
    return
  }

  console.log('Commands: init | touch | fresh [maxAgeMs] | age | state')
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
