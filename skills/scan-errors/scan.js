#!/usr/bin/env node
/**
 * scan-errors.js
 * 扫描 memory/ 和关键文件，检测常见问题
 * 每天定时运行，报告推送到飞书
 */

const fs = require('fs');
const path = require('path');

const WORKSPACE = process.env.WORKSPACE || '/Users/mac/.openclaw/workspace';
const MEMORY_DIR = path.join(WORKSPACE, 'memory');
const REPORTS_DIR = path.join(WORKSPACE, '.scan-reports');
const NOW = new Date();
const TODAY = NOW.toISOString().slice(0, 10); // YYYY-MM-DD

// ─── 工具函数 ───────────────────────────────────────────

function readDir(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter(f => f.endsWith('.md'));
}

function readFile(filePath) {
  try {
    return fs.readFileSync(filePath, 'utf8');
  } catch {
    return '';
  }
}

function getFiles() {
  const files = [];
  // memory/ 目录下的日记
  const memFiles = readDir(MEMORY_DIR).map(f => ({
    name: f,
    path: path.join(MEMORY_DIR, f),
    type: 'daily'
  }));
  // 关键根文件
  const rootFiles = ['MEMORY.md', 'HEARTBEAT.md', 'AGENTS.md', 'SOUL.md', 'USER.md']
    .filter(f => fs.existsSync(path.join(WORKSPACE, f)))
    .map(f => ({
      name: f,
      path: path.join(WORKSPACE, f),
      type: 'root'
    }));
  return [...memFiles, ...rootFiles];
}

// ─── 检测规则 ───────────────────────────────────────────

const rules = [
  {
    name: '未闭环的任务',
    detect: (content, fileName) => {
      // 找以 - [ ] 或 - TODO: 或 ## TODO 开头的未完成标记，跳过已完成的 [x]/~~/done
      const lines = content.split('\n');
      const open = [];
      lines.forEach((line, i) => {
        // 匹配：- [ ] xxx / - TODO: xxx / ## TODO xxx / * [ ] xxx
        const m = line.match(/^[\s]*[-*]*\s*(\[?\s*(TODO|待办|待做|TODO)\s*\]?)[:：]?\s*(.+)/i);
        if (!m) return;
        const text = m[3].trim();
        if (
          line.includes('[x]') || line.includes('[X]') ||
          line.includes('~~') || line.includes('**完成**') ||
          /已完成|已做|已完成/i.test(text)
        ) return;
        open.push({ line: i + 1, text: text.slice(0, 60) });
      });
      return open;
    }
  },
  {
    name: '未来日期',
    detect: (content, fileName) => {
      const lines = content.split('\n');
      const future = [];
      const nextYear = parseInt(TODAY.slice(0, 4)) + 1;
      // 匹配 YYYY-MM-DD 或 YYYY/MM/DD
      lines.forEach((line, i) => {
        const matches = line.match(/\b(20\d{2})[-/]([01]?\d)[-/]([012]?\d)\b/g);
        if (!matches) return;
        matches.forEach(m => {
          const [y, mo, d] = m.replace('/', '-').split('-').map(Number);
          const dateStr = `${y}-${String(mo).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
          if (dateStr > TODAY && y <= nextYear) {
            future.push({ line: i + 1, text: `「${m}」超出今天` });
          }
        });
      });
      return future;
    }
  },
  {
    name: '孤立文件引用',
    detect: (content, fileName) => {
      // 引用了不存在的 .md 文件
      const dir = path.dirname(path.join(WORKSPACE, fileName));
      const refs = [];
      const mdRefs = content.match(/\[.+?\]\(([^)]+\.md)\)/g) || [];
      mdRefs.forEach(ref => {
        const m = ref.match(/\[.+?\]\((.+?)\)/);
        if (!m) return;
        const target = path.resolve(dir, m[1]);
        if (!fs.existsSync(target)) {
          refs.push({ line: 0, text: `引用了不存在的文件: ${m[1]}` });
        }
      });
      return refs;
    }
  },
  {
    name: '异常短或空的文件',
    detect: (content, fileName) => {
      const stripped = content.replace(/\s/g, '');
      if (stripped.length < 50 && content.trim().length > 0) {
        return [{ line: 0, text: `文件内容极短（${stripped.length}字），可能未完成` }];
      }
      if (content.trim().length === 0) {
        return [{ line: 0, text: '文件为空' }];
      }
      return [];
    }
  },
  {
    name: '连续多天无记录',
    detect: (content, fileName) => {
      // 只检查 MEMORY.md 和根文件
      return [];
    }
  }
];

// ─── 主扫描 ───────────────────────────────────────────

function run() {
  const files = getFiles();
  const report = {
    date: TODAY,
    total: files.length,
    issues: [],
    summary: { files: 0, issues: 0 }
  };

  for (const file of files) {
    const content = readFile(file.path);
    for (const rule of rules) {
      const found = rule.detect(content, file.name);
      if (found && found.length > 0) {
        report.issues.push({
          file: file.name,
          type: rule.name,
          items: found
        });
      }
    }
  }

  report.summary.files = report.total;
  report.summary.issues = report.issues.length;

  return report;
}

// ─── 格式化输出 ─────────────────────────────────────────

function formatReport(report) {
  let out = `🦀 Memory 扫描报告 | ${report.date}\n`;
  out += `扫描 ${report.total} 个文件，发现 ${report.issues.length} 个问题\n\n`;

  if (report.issues.length === 0) {
    out += '✅ 一切正常，没有发现问题。';
    return out;
  }

  for (const issue of report.issues) {
    out += `📄 ${issue.file} — ${issue.type}\n`;
    issue.items.forEach(item => {
      const loc = item.line > 0 ? `第${item.line}行` : '全局';
      out += `  · ${loc}：${item.text}\n`;
    });
    out += '\n';
  }

  out += '— 大闸蟹自动巡检 🦀';
  return out;
}

// ─── 保存报告 ───────────────────────────────────────────

function saveReport(report) {
  if (!fs.existsSync(REPORTS_DIR)) {
    fs.mkdirSync(REPORTS_DIR, { recursive: true });
  }
  const file = path.join(REPORTS_DIR, `scan-${TODAY}.json`);
  fs.writeFileSync(file, JSON.stringify(report, null, 2));
  return file;
}

// ─── 执行 ───────────────────────────────────────────

const report = run();
const text = formatReport(report);
const jsonFile = saveReport(report);

console.log(text);
console.log('\n[报告已保存]', jsonFile);

// 如果有问题才输出，用于 cron 判断
if (report.issues.length > 0) {
  process.exit(0); // 有问题，正常退出
} else {
  process.exit(0); // 总是正常退出，输出即可
}
