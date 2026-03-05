const { app } = require('electron')
const path = require('path')
const fs = require('fs')
const fsp = require('fs/promises')

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
        await fsp.writeFile(sessionPath, Buffer.from(sessionContent))
        console.log(`✅ 保存 session (原始文件): ${sessionPath}`)
      } else if (account.session_string) {
        await fsp.writeFile(sessionPath, account.session_string, 'utf8')
        console.log(`✅ 保存 session (session_string): ${sessionPath}`)
      } else {
        console.warn(`⚠️ 无法保存 session: ${account.phone} (无内容)`)
      }

      // 2. Build and save JSON config
      let config
      if (jsonConfig) {
        // Merge user-supplied JSON with authoritative database values
        config = {
          ...jsonConfig,
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
}

module.exports = new LocalSessionManager()
