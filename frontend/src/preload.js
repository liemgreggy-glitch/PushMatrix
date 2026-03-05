const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electron', {
  ipcRenderer: {
    send: (channel, ...args) => {
      const validChannels = ['console-log', 'log-message']
      if (validChannels.includes(channel)) {
        ipcRenderer.send(channel, ...args)
      }
    },
    on: (channel, func) => {
      const validChannels = ['append-log']
      if (validChannels.includes(channel)) {
        ipcRenderer.on(channel, (event, ...args) => func(...args))
      }
    },
    invoke: (channel, ...args) => {
      const validChannels = [
        'get-app-version',
        'save-session-to-local',
        'move-session',
        'update-session-config',
        'delete-session',
        'open-sessions-folder',
        'get-sessions-dir',
        'import-files-locally',
        'scan-local-accounts',
        'watch-sessions',
        'unwatch-sessions',
      ]
      if (validChannels.includes(channel)) {
        return ipcRenderer.invoke(channel, ...args)
      }
    }
  }
})

contextBridge.exposeInMainWorld('electronAPI', {
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  platform: process.platform,
})
