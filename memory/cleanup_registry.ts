/**
 * cleanup_registry.ts
 * 独立的 cleanup registry 模式（供未来 skill 扩展用）
 * 不依赖 OpenClaw
 */

type CleanupFn = () => Promise<void> | void

const cleanupFunctions = new Set<CleanupFn>()

/**
 * 注册清理函数，返回注销函数
 */
export function registerCleanup(fn: CleanupFn): () => void {
  cleanupFunctions.add(fn)
  return () => cleanupFunctions.delete(fn)
}

/**
 * 执行所有已注册的清理函数
 */
export async function runCleanups(): Promise<void> {
  const results = await Promise.allSettled(
    Array.from(cleanupFunctions).map(fn => Promise.resolve(fn()))
  )
  const failures = results.filter((r): r is PromiseRejectedResult => r.status === 'rejected')
  if (failures.length > 0) {
    console.error(`[cleanup] ${failures.length} cleanup(s) failed`)
    failures.forEach((f, i) => console.error(`  [${i + 1}]`, f.reason))
  }
}

/**
 * 清空注册表（测试用）
 */
export function clearCleanups(): void {
  cleanupFunctions.clear()
}

// ── test ─────────────────────────────────────────────────────────────────────

if (require.main === module) {
  // smoke test
  const unregister1 = registerCleanup(async () => {
    console.log('cleanup 1 ran')
  })
  const unregister2 = registerCleanup(() => {
    console.log('cleanup 2 ran (sync)')
  })

  console.log('registered:', cleanupFunctions.size)
  runCleanups().then(() => {
    console.log('done, remaining:', cleanupFunctions.size)
    unregister1()
    unregister2()
    console.log('after unregister:', cleanupFunctions.size)
  })
}
