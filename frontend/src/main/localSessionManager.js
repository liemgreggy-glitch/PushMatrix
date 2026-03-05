const { app } = require('electron')
const path = require('path')
const fs = require('fs')
const fsp = require('fs/promises')

/**
 * Safely convert various binary representations to a Node.js Buffer.
 * Handles: Buffer, ArrayBuffer, Uint8Array, and IPC-serialised Buffer
 * objects ({ type: 'Buffer', data: [...] }).
 */
function toBuffer(val) {
  if (val === null || val === undefined) return null
  if (Buffer.isBuffer(val)) return val
  if (val instanceof ArrayBuffer) return Buffer.from(val)
  if (val instanceof Uint8Array) return Buffer.from(val)
  // IPC passes Buffers as { type: 'Buffer', data: [...] }
  if (typeof val === 'object' && val.type === 'Buffer' && Array.isArray(val.data)) {
    return Buffer.from(val.data)
  }
  // Plain JS Array (e.g. Array.from(new Uint8Array(...)) from the renderer)
  if (Array.isArray(val)) {
    return Buffer.from(val)
  }
  // Plain object with numeric keys (e.g. structured-clone of ArrayBuffer)
  if (typeof val === 'object') {
    try { return Buffer.from(Object.values(val)) } catch { return null }
  }
  return null
}

// Debounce delay (ms) for fs.watch notifications
const WATCH_DEBOUNCE_MS = 300

// Mapping from restriction_status → folder name (Chinese, matches backend)
const STATUS_FOLDERS = {
  UNRESTRICTED: '无限制',
  SPAM: '垃圾邮件',
  FROZEN: '冻结',
  BANNED: '封禁',
  UNKNOWN: '未知错误',
  ERROR: '未知错误',
  UNAUTHORIZED: '未知错误',
  null: '未检查',
}

// Mapping from restriction_status → spamblock string for JSON config
const SPAMBLOCK_MAP = {
  UNRESTRICTED: 'free',
  SPAM: 'spam',
  FROZEN: 'frozen',
  BANNED: 'banned',
  UNKNOWN: 'unknown',
  ERROR: 'unknown',
  UNAUTHORIZED: 'unauthorized',
}

class LocalSessionManager {
  constructor() {
    const isDev = !app.isPackaged

    if (isDev) {
      // Development: sessions folder at project root
      this.baseDir = path.join(process.cwd(), 'sessions')
    } else {
      // Production: sessions folder next to the exe
      this.baseDir = path.join(path.dirname(app.getPath('exe')), 'sessions')
    }

    this._ensureFolders()
    console.log(`📂 Session 文件目录: ${this.baseDir}`)
  }

  /**
   * Ensure all status sub-directories exist.
   */
  _ensureFolders() {
    const uniqueFolders = [...new Set(Object.values(STATUS_FOLDERS))]
    for (const folderName of uniqueFolders) {
      fs.mkdirSync(path.join(this.baseDir, folderName), { recursive: true })
    }
  }

  /**
   * Return the folder path for a given restriction status.
   */
  getFolderPath(restrictionStatus) {
    const folderName = STATUS_FOLDERS[restrictionStatus] || '未检查'
    return path.join(this.baseDir, folderName)
  }

  /**
   * Save .session and .json files from an account object.
   * @param {object} account - Account data from the backend.
   * @param {ArrayBuffer|Buffer|null} sessionContent - Raw binary content of the .session file, if available.
   * @param {object|null} jsonConfig - Parsed JSON config provided alongside the session file, if available.
   */
  async saveSessionFromAccount(account, sessionContent = null, jsonConfig = null) {
    try {
      const folder = this.getFolderPath(account.restriction_status)

      // 1. Save .session file
      const sessionPath = path.join(folder, `${account.phone}.session`)
      if (sessionContent) {
        // Prefer original binary content when supplied
        const buf = toBuffer(sessionContent)
        if (buf) {
          await fsp.writeFile(sessionPath, buf)
          console.log(`✅ 保存 session (原始文件): ${sessionPath}`)
        } else {
          console.warn(`⚠️ 无法转换 sessionContent 为 Buffer: ${account.phone}`)
        }
      } else if (account.session_string) {
        await fsp.writeFile(sessionPath, account.session_string, 'utf8')
        console.log(`✅ 保存 session (session_string): ${sessionPath}`)
      } else {
        console.warn(`⚠️ 无法保存 session: ${account.phone} (无内容)`)
      }

      // 2. Build and save JSON config
      let config
      if (jsonConfig) {
        // Only spread plain objects; ignore null/Buffer/Array/etc.
        const safeJsonConfig = (
          typeof jsonConfig === 'object' &&
          jsonConfig !== null &&
          !Array.isArray(jsonConfig) &&
          !Buffer.isBuffer(jsonConfig)
        ) ? jsonConfig : null
        config = {
          ...(safeJsonConfig || {}),
          ...this._generateStandardConfig(account),
        }
      } else {
        config = this._generateStandardConfig(account)
      }

      const configPath = path.join(folder, `${account.phone}.json`)
      await fsp.writeFile(configPath, JSON.stringify(config, null, 2), 'utf8')
      console.log(`✅ 保存配置: ${configPath}`)

      return { success: true, sessionPath, configPath }
    } catch (err) {
      console.error(`❌ 保存失败 (${account.phone}):`, err)
      return { success: false, error: err.message }
    }
  }

  /**
   * Move .session and .json files from one status folder to another.
   */
  async moveSession(phone, oldStatus, newStatus) {
    try {
      const oldFolder = this.getFolderPath(oldStatus)
      const newFolder = this.getFolderPath(newStatus)

      if (oldFolder === newFolder) {
        console.log(`ℹ️ 文件夹相同，无需移动: ${phone}`)
        return { success: true }
      }

      console.log(`📦 准备移动: ${phone}`)
      console.log(`   从: ${oldFolder}`)
      console.log(`   到: ${newFolder}`)

      const movedFiles = []
      const missingFiles = []

      for (const ext of ['.session', '.json']) {
        const oldFile = path.join(oldFolder, `${phone}${ext}`)
        const newFile = path.join(newFolder, `${phone}${ext}`)
        try {
          await fsp.access(oldFile)
          await fsp.rename(oldFile, newFile)
          console.log(`✅ 移动成功: ${phone}${ext}`)
          movedFiles.push(ext)
        } catch {
          // File doesn't exist in old folder – skip
          console.warn(`⚠️ 源文件不存在: ${oldFile}`)
          missingFiles.push(ext)
        }
      }

      if (missingFiles.length > 0) {
        console.warn(`⚠️ ${phone} 缺少文件: ${missingFiles.join(', ')}`)
      }

      return { success: true, movedFiles, missingFiles }
    } catch (err) {
      console.error(`❌ 移动失败 (${phone}):`, err)
      return { success: false, error: err.message }
    }
  }

  /**
   * Re-write the .json config for an account in its current folder.
   */
  async updateConfig(account) {
    try {
      const folder = this.getFolderPath(account.restriction_status)
      const configPath = path.join(folder, `${account.phone}.json`)
      const config = this._generateStandardConfig(account)
      await fsp.writeFile(configPath, JSON.stringify(config, null, 2), 'utf8')
      console.log(`✅ 更新配置: ${configPath}`)
      return { success: true }
    } catch (err) {
      console.error(`❌ 更新配置失败 (${account.phone}):`, err)
      return { success: false, error: err.message }
    }
  }

  /**
   * Delete .session and .json files for a phone number.
   * If restrictionStatus is given, only that folder is searched;
   * otherwise all folders are checked.
   */
  async deleteSession(phone, restrictionStatus = null) {
    try {
      let folders
      if (restrictionStatus !== null && restrictionStatus !== undefined) {
        folders = [this.getFolderPath(restrictionStatus)]
      } else {
        const uniqueFolders = [...new Set(Object.values(STATUS_FOLDERS))]
        folders = uniqueFolders.map(name => path.join(this.baseDir, name))
      }

      let deleted = false
      for (const folder of folders) {
        for (const ext of ['.session', '.json']) {
          const filePath = path.join(folder, `${phone}${ext}`)
          try {
            await fsp.unlink(filePath)
            console.log(`✅ 删除: ${filePath}`)
            deleted = true
          } catch {
            // File doesn't exist – skip
          }
        }
      }

      return { success: true, deleted }
    } catch (err) {
      console.error(`❌ 删除失败 (${phone}):`, err)
      return { success: false, error: err.message }
    }
  }

  /**
   * Generate the standard JSON config from an account object.
   */
  _generateStandardConfig(account) {
    return {
      app_id: account.api_id || 2040,
      app_hash: account.api_hash || 'b18441a1ff607e10a989891a5462e627',
      sdk: 'Windows 10 x64',
      device: 'PushMatrix',
      app_version: '6.6.2 x64',
      twoFA: account.two_fa || null,
      id: account.telegram_id ? parseInt(account.telegram_id, 10) : null,
      phone: account.phone,
      username: account.username || null,
      first_name: account.first_name || null,
      last_name: account.last_name || null,
      spamblock: SPAMBLOCK_MAP[account.restriction_status] || 'unknown',
      session_file: account.phone,
      last_connect_date: account.last_used_at || null,
      session_created_date: account.created_at || new Date().toISOString(),
      last_check_time: account.restriction_checked_at
        ? Math.floor(new Date(account.restriction_checked_at).getTime() / 1000)
        : null,
      block: account.is_banned || false,
    }
  }

  getBaseDir() {
    return this.baseDir
  }

  /**
   * Scan all status sub-folders and return an account list derived from
   * the .json config files found on disk.
   */
  async scanAllAccounts() {
    const accounts = []
    const statusFolders = Object.entries(STATUS_FOLDERS)
    const seen = new Set()
    for (const [, folderName] of statusFolders) {
      const folderPath = path.join(this.baseDir, folderName)
      try {
        const files = await fsp.readdir(folderPath)
        for (const file of files) {
          if (!file.endsWith('.json')) continue
          const jsonPath = path.join(folderPath, file)
          try {
            const content = await fsp.readFile(jsonPath, 'utf8')
            const config = JSON.parse(content)
            const phone = config.phone || file.replace('.json', '')
            if (seen.has(phone)) continue
            seen.add(phone)
            const sessionPath = path.join(folderPath, `${phone}.session`)
            let hasSession = false
            try { await fsp.access(sessionPath); hasSession = true } catch {}
            accounts.push({
              phone,
              username: config.username || null,
              first_name: config.first_name || null,
              last_name: config.last_name || null,
              api_id: config.app_id || null,
              api_hash: config.app_hash || null,
              two_fa: config.twoFA || null,
              two_fa_enabled: !!config.twoFA,
              telegram_id: config.id ? String(config.id) : null,
              restriction_status: this._folderToStatus(folderName),
              spamblock: config.spamblock || 'unknown',
              session_file: phone,
              has_session: hasSession,
              _localFolder: folderName,
              _jsonPath: jsonPath,
            })
          } catch {}
        }
      } catch {}
    }
    return accounts
  }

  /**
   * Map a folder name back to a restriction_status string.
   * Derived from STATUS_FOLDERS to keep a single source of truth.
   * When multiple statuses map to the same folder, prefer the canonical one.
   */
  _folderToStatus(folderName) {
    for (const [status, folder] of Object.entries(STATUS_FOLDERS)) {
      if (folder === folderName && status !== 'ERROR' && status !== 'UNAUTHORIZED') {
        return status === 'null' || status === null ? null : status
      }
    }
    return null
  }

  /**
   * Watch the sessions base directory for file changes.
   * Calls `callback` (debounced 300 ms) on every .json / .session change.
   */
  watchSessions(callback) {
    if (this._watcher) return
    let debounceTimer = null
    this._watcher = fs.watch(this.baseDir, { recursive: true }, (eventType, filename) => {
      if (!filename) return
      const lower = filename.toLowerCase()
      if (!lower.endsWith('.json') && !lower.endsWith('.session')) return
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        callback({ eventType, filename })
      }, WATCH_DEBOUNCE_MS)
    })
  }

  /**
   * Stop watching the sessions directory.
   */
  unwatchSessions() {
    if (this._watcher) {
      this._watcher.close()
      this._watcher = null
    }
  }

  /**
   * Pure local import: accepts an array of { name, buffer } objects,
   * pairs .session + .json files, and writes them to sessions/未检查/.
   */
  async importFilesLocally(fileList) {
    const results = { success: 0, failed: 0, details: [] }
    const targetFolder = path.join(this.baseDir, '未检查')

    const sessionFiles = fileList.filter(f => f.name.endsWith('.session'))
    const jsonFiles = fileList.filter(f => f.name.endsWith('.json'))

    // Process accounts that have a .session file
    for (const sf of sessionFiles) {
      const phone = sf.name.replace('.session', '')
      const jf = jsonFiles.find(f => f.name === `${phone}.json`)
      try {
        const sessionBuf = toBuffer(sf.buffer)
        if (!sessionBuf || sessionBuf.length === 0) throw new Error('无法转换 session 文件内容为 Buffer')
        await fsp.writeFile(path.join(targetFolder, sf.name), sessionBuf)
        let config = {}
        if (jf) {
          try {
            const jsonBuf = toBuffer(jf.buffer)
            config = JSON.parse(jsonBuf ? jsonBuf.toString('utf8') : '{}')
          } catch {}
          await fsp.writeFile(path.join(targetFolder, jf.name), JSON.stringify(config, null, 2), 'utf8')
        } else {
          config = { phone, session_file: phone, spamblock: 'unknown' }
          await fsp.writeFile(path.join(targetFolder, `${phone}.json`), JSON.stringify(config, null, 2), 'utf8')
        }
        results.success++
        results.details.push({ filename: sf.name, phone, success: true, message: '导入成功' })
      } catch (err) {
        results.failed++
        results.details.push({ filename: sf.name, phone, success: false, message: err.message })
      }
    }

    // Process JSON-only entries (no matching .session)
    for (const jf of jsonFiles) {
      const phone = jf.name.replace('.json', '')
      if (sessionFiles.some(f => f.name === `${phone}.session`)) continue
      try {
        const jsonBuf = toBuffer(jf.buffer)
        const config = JSON.parse(jsonBuf ? jsonBuf.toString('utf8') : '{}')
        await fsp.writeFile(path.join(targetFolder, jf.name), JSON.stringify(config, null, 2), 'utf8')
        results.success++
        results.details.push({ filename: jf.name, phone, success: true, message: '仅导入配置' })
      } catch (err) {
        results.failed++
        results.details.push({ filename: jf.name, phone, success: false, message: err.message })
      }
    }

    return results
  }
}

module.exports = new LocalSessionManager()
