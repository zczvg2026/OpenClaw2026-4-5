/**
 * memory_caps.ts
 * MEMORY.md 双重截断（200行 + 25KB）
 * 独立脚本，不依赖 OpenClaw
 */

import { promises as fs } from 'fs'

const MEMORY_FILE = '/Users/mac/.openclaw/workspace/MEMORY.md'
const MAX_MEMORY_LINES = 200
const MAX_MEMORY_BYTES = 25_000

interface CapResult {
  content: string
  wasTruncated: boolean
  reason: string | null
}

/**
 * 先按行截断（>200行切到200行）
 * 再按字节截断（>25KB找到最后一个换行符cut）
 * 超限时 append warning
 */
export function checkMemoryCap(content: string): CapResult {
  let result = content
  let wasTruncated = false
  let reason: string | null = null

  // Step 1: 行数截断
  const lines = result.split('\n')
  if (lines.length > MAX_MEMORY_LINES) {
    result = lines.slice(0, MAX_MEMORY_LINES).join('\n')
    wasTruncated = true
    reason = `超过 ${MAX_MEMORY_LINES} 行`
  }

  // Step 2: 字节截断
  const encoder = new TextEncoder()
  if (encoder.encode(result).length > MAX_MEMORY_BYTES) {
    // 找到最后一个换行符，在那里cut
    let cut = MAX_MEMORY_BYTES
    const bytes = encoder.encode(result)
    for (let i = MAX_MEMORY_BYTES - 1; i >= 0; i--) {
      if (bytes[i] === 10) { // \n
        cut = i
        break
      }
    }
    result = result.slice(0, cut)
    wasTruncated = true
    reason = `超过 ${MAX_MEMORY_BYTES.toLocaleString()} 字节`
  }

  // Append warning
  if (wasTruncated && reason) {
    result += `\n\n> ⚠️ MEMORY.md 超过容量限制（${reason}），只加载了部分内容。精简索引条目（每条≤200字符），把详细内容移到 topic 文件。`
  }

  return { content: result, wasTruncated, reason }
}

/**
 * 读取 MEMORY.md，若超限则截断并写回
 */
export async function truncateMemoryMd(): Promise<CapResult> {
  let raw: string
  try {
    raw = await fs.readFile(MEMORY_FILE, 'utf-8')
  } catch {
    return { content: '', wasTruncated: false, reason: null }
  }

  const result = checkMemoryCap(raw)

  if (result.wasTruncated) {
    await fs.writeFile(MEMORY_FILE, result.content, 'utf-8')
    console.log(`[memory_caps] truncated: ${result.reason}`)
  }

  return result
}

// ── CLI ─────────────────────────────────────────────────────────────────────

async function main() {
  const cmd = process.argv[2]

  if (cmd === 'check') {
    const raw = await fs.readFile(MEMORY_FILE, 'utf-8')
    const r = checkMemoryCap(raw)
    console.log(`wasTruncated: ${r.wasTruncated}`)
    console.log(`reason: ${r.reason}`)
    console.log(`bytes: ${new TextEncoder().encode(r.content).length}`)
    console.log(`lines: ${r.content.split('\n').length}`)
    return
  }

  if (cmd === 'truncate') {
    const r = await truncateMemoryMd()
    console.log(`✅ truncated: ${r.wasTruncated}, reason: ${r.reason}`)
    return
  }

  console.log('Commands: check | truncate')
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
