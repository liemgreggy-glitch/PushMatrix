/**
 * 账号限制检查专用日志工具
 * 输出格式: [HH:MM:SS] 消息  — 无 INFO/WARN/ERROR 级别前缀
 * 支持按状态着色（浏览器控制台使用 CSS，Electron 主进程使用 ANSI）
 */

// ANSI 颜色码（用于 Electron 主进程终端）
const ANSI = {
  reset: '\x1b[0m',
  white: '\x1b[37m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[36m',
  red: '\x1b[31m',
  dimYellow: '\x1b[2m\x1b[33m',
}

// CSS 颜色（用于浏览器 / Electron 渲染进程控制台）
const CSS = {
  white: 'color: #d1d5db',
  green: 'color: #10b981',
  yellow: 'color: #f59e0b',
  blue: 'color: #38bdf8',
  red: 'color: #ef4444',
  dimYellow: 'color: #fbbf24; opacity: 0.8',
}

// 状态 → 样式映射
const STATUS_CONFIG = {
  UNRESTRICTED: { cssColor: CSS.green, ansiColor: ANSI.green, emoji: '✅', text: '无限制' },
  SPAM: { cssColor: CSS.yellow, ansiColor: ANSI.yellow, emoji: '⚠️', text: '垃圾邮件' },
  FROZEN: { cssColor: CSS.blue, ansiColor: ANSI.blue, emoji: '❄️', text: '冻结' },
  BANNED: { cssColor: CSS.red, ansiColor: ANSI.red, emoji: '🚫', text: '封禁' },
  UNKNOWN: { cssColor: CSS.dimYellow, ansiColor: ANSI.dimYellow, emoji: '❓', text: '未知/错误' },
  ERROR: { cssColor: CSS.red, ansiColor: ANSI.red, emoji: '❌', text: '检查失败' },
  UNAUTHORIZED: { cssColor: CSS.dimYellow, ansiColor: ANSI.dimYellow, emoji: '❓', text: '未授权' },
}

// 是否在 Electron 环境
const isElectron =
  typeof window !== 'undefined' && window.electron?.ipcRenderer !== undefined

/** 格式化当前时间为 [HH:MM:SS] */
function getTimestamp() {
  const now = new Date()
  const h = String(now.getHours()).padStart(2, '0')
  const m = String(now.getMinutes()).padStart(2, '0')
  const s = String(now.getSeconds()).padStart(2, '0')
  return `[${h}:${m}:${s}]`
}

/**
 * 向 Electron 主进程发送带 ANSI 颜色的日志（显示在终端）
 * @param {string} message
 * @param {string} ansiColor
 */
function sendToMain(message, ansiColor = ANSI.white) {
  if (!isElectron) return
  window.electron.ipcRenderer.send('log-message', {
    level: 'info',
    message: `${ansiColor}${message}${ANSI.reset}`,
    data: null,
  })
}

/**
 * 输出一条检查日志（普通文字，白色）
 * @param {string} message
 */
export function logCheck(message) {
  const ts = getTimestamp()
  const full = `${ts} ${message}`
  console.log(`%c${full}`, CSS.white)
  sendToMain(full, ANSI.white)
}

/**
 * 输出账号检查结果行（带颜色）
 * @param {number} index   当前序号（1-based）
 * @param {number} total   账号总数
 * @param {string} phone   手机号
 * @param {string} status  UNRESTRICTED | SPAM | FROZEN | BANNED | UNKNOWN | ERROR | UNAUTHORIZED
 */
export function logCheckResult(index, total, phone, status) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.UNKNOWN
  const ts = getTimestamp()
  const message = `[${index}/${total}] ${phone} → ${cfg.emoji} ${cfg.text}`
  const full = `${ts} ${message}`
  console.log(`%c${full}`, cfg.cssColor)
  sendToMain(full, cfg.ansiColor)
}

/**
 * 输出最终统计结果
 * @param {{ unrestricted: number, spam: number, frozen: number, banned: number, unknown: number }} stats
 */
export function logCheckStats(stats) {
  logCheck(`✅ 检查完成！最终统计：`)
  if (stats.unrestricted > 0) {
    const ts = getTimestamp()
    const msg = `${ts} ✅ 无限制: ${stats.unrestricted}`
    console.log(`%c${msg}`, CSS.green)
    sendToMain(msg, ANSI.green)
  }
  if (stats.spam > 0) {
    const ts = getTimestamp()
    const msg = `${ts} ⚠️ 垃圾邮件限制: ${stats.spam}`
    console.log(`%c${msg}`, CSS.yellow)
    sendToMain(msg, ANSI.yellow)
  }
  if (stats.frozen > 0) {
    const ts = getTimestamp()
    const msg = `${ts} ❄️ 冻结: ${stats.frozen}`
    console.log(`%c${msg}`, CSS.blue)
    sendToMain(msg, ANSI.blue)
  }
  if (stats.banned > 0) {
    const ts = getTimestamp()
    const msg = `${ts} 🚫 封禁: ${stats.banned}`
    console.log(`%c${msg}`, CSS.red)
    sendToMain(msg, ANSI.red)
  }
  if (stats.unknown > 0) {
    const ts = getTimestamp()
    const msg = `${ts} ❓ 未知/错误: ${stats.unknown}`
    console.log(`%c${msg}`, CSS.dimYellow)
    sendToMain(msg, ANSI.dimYellow)
  }
}

export default { logCheck, logCheckResult, logCheckStats }
