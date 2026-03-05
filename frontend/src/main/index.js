const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')

const isDev = process.env.NODE_ENV === 'development'

let mainWindow = null
let consoleWindow = null

// 发送日志到控制台窗口
function sendLog(level, message, data = null) {
  if (consoleWindow && !consoleWindow.isDestroyed()) {
    const timestamp = new Date().toLocaleTimeString('zh-CN', { hour12: false })
    consoleWindow.webContents.send('append-log', {
      level,
      message,
      timestamp,
      data
    })
  }
}

// 创建控制台窗口（第一个启动）
function createConsoleWindow() {
  consoleWindow = new BrowserWindow({
    width: 900,
    height: 600,
    title: 'PushMatrix - 控制台',
    backgroundColor: '#0a0a0a',
    autoHideMenuBar: true,
    resizable: true,
    minimizable: true,
    maximizable: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  })

  consoleWindow.loadFile(path.join(__dirname, '../console.html'))

  consoleWindow.on('closed', () => {
    consoleWindow = null
  })

  // 控制台窗口准备好后，创建主窗口
  consoleWindow.webContents.on('did-finish-load', () => {
    sendLog('success', 'PushMatrix 控制台已启动')
    sendLog('info', '正在启动主应用...')

    // 延迟 500ms 后创建主窗口，确保控制台先显示
    setTimeout(() => {
      createMainWindow()
    }, 500)
  })

  return consoleWindow
}

// 创建主窗口（第二个启动）
function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1024,
    minHeight: 680,
    webPreferences: {
      preload: path.join(__dirname, '../preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    titleBarStyle: 'default',
    backgroundColor: '#1E1E2E',
    show: false,
  })

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
  } else {
    mainWindow.loadFile(path.join(__dirname, '../../dist/renderer/index.html'))
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
    sendLog('success', '主应用窗口已启动')
  })

  mainWindow.on('closed', () => {
    sendLog('warn', '主应用窗口已关闭')
    mainWindow = null
    // 主窗口关闭时，也关闭控制台
    if (consoleWindow && !consoleWindow.isDestroyed()) {
      consoleWindow.close()
    }
  })
}

app.whenReady().then(() => {
  // 先创建控制台窗口
  createConsoleWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createConsoleWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// IPC: 接收前端日志
ipcMain.on('console-log', (event, level, message, data) => {
  sendLog(level, message, data)
  console[level] && console[level](message, data || '')
})

// IPC: 接收自定义日志
ipcMain.on('log-message', (event, data) => {
  sendLog(data.level || 'info', data.message, data.data)
})

// IPC handlers
ipcMain.handle('get-app-version', () => app.getVersion())
