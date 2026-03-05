// 自定义日志工具

const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  SUCCESS: 2,
  WARN: 3,
  ERROR: 4,
}

const LOG_CONFIG = {
  // 日志级别（只显示此级别及以上的日志）
  level: LOG_LEVELS.INFO,

  // API 日志配置
  api: {
    enabled: false,    // 默认关闭 API 详细日志
    showSuccess: false, // 不显示成功的 API 响应
    showRequest: true,  // 显示请求（精简版）
    showError: true,    // 显示错误响应
  },

  // 业务日志配置
  business: {
    enabled: true,      // 业务逻辑日志默认开启
    showDetails: true,  // 显示详细信息
  },
}

class Logger {
  constructor() {
    this.config = { ...LOG_CONFIG }
    // 检查是否在 Electron 环境
    this.isElectron = typeof window !== 'undefined' && window.electron?.ipcRenderer !== undefined
  }

  // 设置日志配置
  setConfig(config) {
    this.config = { ...this.config, ...config }
  }

  // 发送到主进程控制台
  _send(level, message, data = null) {
    if (this.isElectron) {
      window.electron.ipcRenderer.send('log-message', {
        level,
        message,
        data: data ? (typeof data === 'object' ? JSON.stringify(data, null, 2) : data) : null,
      })
    }

    // 同时输出到浏览器控制台
    const consoleFn = console[level] || console.log
    if (data) {
      consoleFn(`[${level.toUpperCase()}]`, message, data)
    } else {
      consoleFn(`[${level.toUpperCase()}]`, message)
    }
  }

  // API 日志（精简版）
  apiRequest(method, url) {
    if (!this.config.api.enabled || !this.config.api.showRequest) return
    const path = url.replace(/^https?:\/\/[^/]+/, '')
    this._send('info', `🔵 ${method.toUpperCase()} ${path}`)
  }

  apiSuccess(url, status = 200) {
    if (!this.config.api.enabled || !this.config.api.showSuccess) return
    const path = url.replace(/^https?:\/\/[^/]+/, '')
    this._send('info', `✅ ${status} ${path}`)
  }

  apiError(url, status, error) {
    if (!this.config.api.enabled || !this.config.api.showError) return
    const path = String(url || '').replace(/^https?:\/\/[^/]+/, '')
    this._send('error', `❌ ${status} ${path}`, error)
  }

  // 业务日志（详细版）
  task(taskName, message, data = null) {
    if (!this.config.business.enabled) return
    this._send('info', `📋 [${taskName}] ${message}`, data)
  }

  taskSuccess(taskName, message, data = null) {
    if (!this.config.business.enabled) return
    this._send('info', `✅ [${taskName}] ${message}`, data)
  }

  taskError(taskName, message, error = null) {
    if (!this.config.business.enabled) return
    this._send('error', `❌ [${taskName}] ${message}`, error)
  }

  // 兼容旧 API（保留以向后兼容，不受新配置开关约束）
  /** @deprecated 请使用 task/taskSuccess/taskError 或 info/warn/error 代替 */
  log(level, message, data = null) {
    const msg = typeof message === 'object' ? JSON.stringify(message) : String(message)
    if (this.isElectron) {
      window.electron.ipcRenderer.send('console-log', level, msg, data)
    } else {
      const fn = console[level] || console.log
      fn(message, data || '')
    }
  }

  info(message, data) {
    this._send('info', message, data)
  }

  warn(message, data) {
    this._send('warn', message, data)
  }

  error(message, data) {
    this._send('error', message, data)
  }

  success(message, data) {
    this._send('info', message, data)
  }

  debug(message, data) {
    this._send('log', message, data)
  }
}

const logger = new Logger()

export default logger
