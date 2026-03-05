// 自定义日志工具
class Logger {
  constructor() {
    // 检查是否在 Electron 环境
    this.isElectron = window.electron?.ipcRenderer !== undefined
  }

  log(level, message, data = null) {
    const msg = typeof message === 'object' ? JSON.stringify(message) : String(message)

    if (this.isElectron) {
      window.electron.ipcRenderer.send('console-log', level, msg, data)
    } else {
      console[level] && console[level](message, data || '')
    }
  }

  info(message, data) {
    this.log('info', message, data)
  }

  warn(message, data) {
    this.log('warn', message, data)
  }

  error(message, data) {
    this.log('error', message, data)
  }

  success(message, data) {
    this.log('success', message, data)
  }

  debug(message, data) {
    this.log('debug', message, data)
  }
}

export default new Logger()
