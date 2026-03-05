<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">批量导入</span>
    </div>

    <div class="import-container">
      <!-- 左侧：导入方式 -->
      <div class="import-left">
        <h3 class="section-title">选择导入方式</h3>

        <el-tabs v-model="activeTab" class="import-tabs">
          <!-- 文件导入 -->
          <el-tab-pane label="文件导入" name="file">
            <div
              class="upload-area"
              :class="{ 'is-dragover': isDragover }"
              @drop="handleDrop"
              @dragover="handleDragOver"
              @dragleave="handleDragLeave"
              @click="triggerFileSelect"
            >
              <el-icon :size="48" color="#409EFF"><Upload /></el-icon>
              <p class="upload-text">拖拽文件到此处，或点击上传</p>
              <p class="upload-hint">支持 Session (.session)、压缩包 (.zip, .rar)、文件夹</p>
              <p class="upload-warning">不支持 Excel (.xlsx)、CSV (.csv)、TXT (.txt) 格式</p>
            </div>

            <input
              ref="fileInput"
              type="file"
              multiple
              webkitdirectory
              directory
              style="display: none"
              @change="handleFileSelect"
            />

            <div class="action-buttons">
              <el-button @click="triggerFileSelect" icon="FolderOpened">选择文件夹</el-button>
              <el-button @click="triggerSingleFileSelect" icon="Document">选择文件</el-button>
              <el-button @click="downloadTemplate" icon="Download">下载模板</el-button>
            </div>

            <input
              ref="singleFileInput"
              type="file"
              multiple
              accept=".session,.zip,.rar"
              style="display: none"
              @change="handleFileSelect"
            />
          </el-tab-pane>

          <!-- Session 导入 -->
          <el-tab-pane label="Session 导入" name="session">
            <el-form label-width="100px">
              <el-form-item label="Session 字符串">
                <el-input
                  v-model="sessionForm.session_string"
                  type="textarea"
                  :rows="6"
                  placeholder="粘贴 Pyrogram 或 Telethon Session 字符串"
                />
              </el-form-item>
              <el-form-item label="手机号">
                <el-input v-model="sessionForm.phone" placeholder="+1234567890" />
              </el-form-item>
              <el-form-item label="API ID">
                <el-input v-model="sessionForm.api_id" placeholder="Telegram API ID" />
              </el-form-item>
              <el-form-item label="API Hash">
                <el-input v-model="sessionForm.api_hash" placeholder="Telegram API Hash" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="importSession" :loading="importing">
                  开始导入
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <!-- 手动输入 -->
          <el-tab-pane label="手动输入" name="manual">
            <el-form label-width="100px">
              <el-form-item label="手机号" required>
                <el-input v-model="manualForm.phone" placeholder="+1234567890" />
              </el-form-item>
              <el-form-item label="API ID" required>
                <el-input v-model="manualForm.api_id" placeholder="Telegram API ID" />
              </el-form-item>
              <el-form-item label="API Hash" required>
                <el-input v-model="manualForm.api_hash" placeholder="Telegram API Hash" />
              </el-form-item>
              <el-form-item label="代理">
                <el-select v-model="manualForm.proxy_id" clearable placeholder="选择代理（可选）" style="width: 100%">
                  <el-option label="无代理" :value="null" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="addManual" :loading="importing">
                  添加账号
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 右侧：导入结果 -->
      <div class="import-right">
        <h3 class="section-title">导入结果</h3>

        <div v-if="importResults.length === 0" class="empty-result">
          <el-icon :size="64" color="#909399"><Box /></el-icon>
          <p>等待导入...</p>
        </div>

        <div v-else class="result-list">
          <div class="result-summary">
            <el-tag type="success">成功: {{ successCount }}</el-tag>
            <el-tag type="danger">失败: {{ failCount }}</el-tag>
            <el-tag type="info">总计: {{ importResults.length }}</el-tag>
          </div>

          <el-table :data="importResults" max-height="400">
            <el-table-column label="文件名" prop="filename" width="200" />
            <el-table-column label="手机号" prop="phone" width="150" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.success" type="success" size="small">成功</el-tag>
                <el-tag v-else type="danger" size="small">失败</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="信息" prop="message" />
          </el-table>
        </div>

        <h3 class="section-title" style="margin-top: 24px">导入说明</h3>
        <ul class="import-instructions">
          <li>Session 格式：Pyrogram 或 Telethon Session 字符串</li>
          <li>压缩包格式：ZIP 或 RAR，内含 .session 文件和对应的 .json 配置</li>
          <li>JSON 配置示例：<code>{"phone": "+1234567890", "api_id": 12345, "api_hash": "xxx"}</code></li>
          <li>如果只有 .session 文件，系统会自动生成默认配置</li>
          <li>批量导入上限：单次最多 500 个账号</li>
        </ul>
      </div>
    </div>

    <!-- 导入进度对话框 -->
    <el-dialog v-model="showProgress" title="正在导入" width="500px" :close-on-click-modal="false" :close-on-press-escape="false" :show-close="false">
      <div style="padding: 8px 0;">
        <div style="margin-bottom: 16px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="color: #909399;">总进度</span>
            <span style="color: #409eff; font-weight: bold;">{{ importProgress }}%</span>
          </div>
          <el-progress :percentage="importProgress" :status="importStatus" :stroke-width="20" />
        </div>

        <div v-if="totalBatches > 1" style="margin-bottom: 16px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="color: #909399;">当前批次</span>
            <span style="color: #909399;">{{ currentBatch }} / {{ totalBatches }}</span>
          </div>
          <el-progress :percentage="batchProgress" :stroke-width="10" />
        </div>

        <p style="text-align: center; margin-top: 16px; color: #909399;">
          {{ importProgressText }}
        </p>
      </div>

      <template v-if="importStatus !== ''" #footer>
        <el-button @click="showProgress = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { accountsApi } from '../../api/index.js'
import logger from '../../utils/logger.js'

const isElectron = computed(() => {
  return typeof window !== 'undefined' && window.electron !== undefined
})

const activeTab = ref('file')
const isDragover = ref(false)
const importing = ref(false)
const showProgress = ref(false)
const importProgress = ref(0)
const batchProgress = ref(0)
const currentBatch = ref(0)
const totalBatches = ref(0)
const importStatus = ref('')
const importProgressText = ref('')
const importResults = ref([])

const fileInput = ref(null)
const singleFileInput = ref(null)

const sessionForm = ref({
  session_string: '',
  phone: '',
  api_id: '',
  api_hash: '',
})

const manualForm = ref({
  phone: '',
  api_id: '',
  api_hash: '',
  proxy_id: null,
})

const successCount = computed(() => importResults.value.filter(r => r.success).length)
const failCount = computed(() => importResults.value.filter(r => !r.success).length)

// 拖拽事件
function handleDragOver(e) {
  e.preventDefault()
  isDragover.value = true
}

function handleDragLeave(e) {
  e.preventDefault()
  isDragover.value = false
}

async function handleDrop(e) {
  e.preventDefault()
  isDragover.value = false

  const items = e.dataTransfer.items
  const files = []

  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    if (item.kind === 'file') {
      const entry = item.webkitGetAsEntry()
      if (entry) {
        await processEntry(entry, files)
      }
    }
  }

  logger.task('导入', `拖拽了 ${files.length} 个文件`, { fileNames: files.map(f => f.name) })

  if (files.length > 0) {
    await processFiles(files)
  } else {
    ElMessage.warning('请拖拽文件到此处')
  }
}

// 递归处理文件夹
async function processEntry(entry, files) {
  if (entry.isFile) {
    const file = await new Promise((resolve) => entry.file(resolve))
    files.push(file)
  } else if (entry.isDirectory) {
    const reader = entry.createReader()
    const entries = await new Promise((resolve) => reader.readEntries(resolve))
    for (const subEntry of entries) {
      await processEntry(subEntry, files)
    }
  }
}

// 触发文件夹选择
function triggerFileSelect() {
  logger.task('导入', '打开文件夹选择器')
  fileInput.value.click()
}

// 触发单文件选择
function triggerSingleFileSelect() {
  logger.task('导入', '打开文件选择器')
  singleFileInput.value.click()
}

// 文件选择
async function handleFileSelect(e) {
  const files = Array.from(e.target.files)
  logger.task('导入', `用户选择了 ${files.length} 个文件`, { fileNames: files.map(f => f.name) })
  if (files.length > 0) {
    await processFiles(files)
  }
  e.target.value = '' // 清空，允许重复选择
}

// 处理文件
async function processFiles(files) {
  logger.task('导入', '开始处理文件', { totalFiles: files.length })

  // 过滤不支持的格式
  const unsupportedFiles = files.filter(f => {
    const ext = f.name.toLowerCase().split('.').pop()
    return ['xlsx', 'csv', 'txt'].includes(ext)
  })

  if (unsupportedFiles.length > 0) {
    ElMessage.warning(`不支持的格式：${unsupportedFiles.map(f => f.name).join(', ')}`)
  }

  // 筛选支持的文件
  const supportedFiles = files.filter(f => {
    const ext = f.name.toLowerCase().split('.').pop()
    return ['session', 'zip', 'rar', 'json'].includes(ext)
  })

  const sessionCount = supportedFiles.filter(f => f.name.toLowerCase().endsWith('.session')).length
  const jsonCount = supportedFiles.filter(f => f.name.toLowerCase().endsWith('.json')).length
  const archiveCount = supportedFiles.filter(f => {
    const ext = f.name.toLowerCase().split('.').pop()
    return ext === 'zip' || ext === 'rar'
  }).length

  logger.task('导入', '文件分类完成', {
    sessionCount,
    jsonCount,
    archiveCount,
    total: supportedFiles.length,
  })

  if (supportedFiles.length === 0) {
    logger.taskError('导入', '未找到有效的 .session 或 .json 文件')
    ElMessage.error('没有可导入的文件')
    return
  }

  if (supportedFiles.length > 500) {
    ElMessage.error('单次最多导入 500 个文件')
    return
  }

  // 开始导入
  importing.value = true
  showProgress.value = true
  importProgress.value = 0
  batchProgress.value = 0
  currentBatch.value = 0
  totalBatches.value = 0
  importResults.value = []
  importStatus.value = ''

  if (isElectron.value) {
    // Electron: write files directly to local sessions/未检查/ folder
    importProgressText.value = `正在导入 ${supportedFiles.length} 个文件到本地...`
    try {
      const fileList = []
      for (const file of supportedFiles) {
        const buffer = await readFileAsArrayBuffer(file)
        fileList.push({ name: file.name, buffer: Array.from(new Uint8Array(buffer)) })
      }
      const result = await window.electron.ipcRenderer.invoke('import-files-locally', { fileList })
      const safeResult = (result && typeof result === 'object') ? result : { success: 0, failed: 0, details: [] }
      importResults.value = safeResult.details || []
      importProgress.value = 100
      importStatus.value = safeResult.success > 0 ? 'success' : 'exception'
      importProgressText.value = `导入完成！成功 ${safeResult.success} 个，失败 ${safeResult.failed} 个`
      if (safeResult.success > 0) {
        setTimeout(() => { showProgress.value = false }, 2000)
        ElMessage.success(`成功导入 ${safeResult.success} 个账号到本地`)
      } else {
        ElMessage.error('全部导入失败！请检查文件格式')
      }
    } catch (err) {
      importStatus.value = 'exception'
      importProgressText.value = '导入失败：' + (err.message || '未知错误')
      ElMessage.error('导入失败')
    } finally {
      importing.value = false
    }
    return
  }

  // Non-Electron: upload to backend server in batches
  const batchSize = 10
  const batches = []
  for (let i = 0; i < supportedFiles.length; i += batchSize) {
    batches.push(supportedFiles.slice(i, i + batchSize))
  }

  totalBatches.value = batches.length
  importProgressText.value = `准备上传 ${supportedFiles.length} 个文件（共 ${batches.length} 批）...`

  logger.task('导入', `准备上传 ${supportedFiles.length} 个文件到后端，分 ${batches.length} 批`)

  let allDetails = []
  let totalSuccess = 0
  let totalFailed = 0

  try {
    for (let i = 0; i < batches.length; i++) {
      const batch = batches[i]
      currentBatch.value = i + 1
      batchProgress.value = 0
      importProgressText.value = `正在上传第 ${i + 1}/${batches.length} 批 (${batch.length} 个文件)...`

      logger.task('导入', `上传第 ${i + 1}/${batches.length} 批`)

      const formData = new FormData()
      batch.forEach(file => formData.append('files', file))

      try {
        const result = await accountsApi.importFiles(formData, (progress) => {
          batchProgress.value = Math.round(progress * 100)
          if (batchProgress.value % 10 === 0) {
            logger.task('导入', `第 ${i + 1} 批上传进度: ${batchProgress.value}%`)
          }
        })

        // Guard: result may be undefined if the interceptor returns nothing
        const safeResult = (result && typeof result === 'object') ? result : {}
        totalSuccess += safeResult.success || 0
        totalFailed  += safeResult.failed  || 0
        const details = Array.isArray(safeResult.details) ? safeResult.details : []
        allDetails.push(...details)

        logger.taskSuccess('导入', `第 ${i + 1} 批完成`, { success: safeResult.success, failed: safeResult.failed })

        // Batch delay to avoid overloading the server
        if (i < batches.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 500))
        }
      } catch (err) {
        // Try to read structured error info from the axios response body
        const errData = err?.response?.data
        if (errData && typeof errData === 'object') {
          totalSuccess += errData.success || 0
          totalFailed  += errData.failed  ?? batch.length
          const errDetails = Array.isArray(errData.details) ? errData.details : []
          allDetails.push(...errDetails)
          logger.taskError('导入', `第 ${i + 1} 批失败`, errData.message || err.message)
        } else {
          totalFailed += batch.length
          logger.taskError('导入', `第 ${i + 1} 批失败`, err.message)
        }
      }

      // Update overall progress
      importProgress.value = Math.round(((i + 1) / batches.length) * 100)
    }

    importResults.value = allDetails
    importProgress.value = 100
    batchProgress.value = 100
    importStatus.value = totalSuccess > 0 ? 'success' : 'exception'
    importProgressText.value = `导入完成！成功 ${totalSuccess} 个，失败 ${totalFailed} 个`

    logger.taskSuccess('导入', '全部批次完成', { success: totalSuccess, failed: totalFailed })

    if (totalSuccess > 0) {
      setTimeout(() => { showProgress.value = false }, 2000)
      ElMessage.success(`成功导入 ${totalSuccess} 个账号`)
      // Save newly imported accounts to the local sessions directory
      if (isElectron.value) {
        await saveImportedAccountsToLocal(allDetails, supportedFiles)
      }
    } else {
      ElMessage.error('全部导入失败！请检查文件格式')
    }
  } catch (err) {
    importStatus.value = 'exception'
    importProgressText.value = '导入失败：' + (err.message || '未知错误')
    logger.taskError('导入', '导入失败', err.message)
    ElMessage.error('导入失败')
  } finally {
    importing.value = false
  }
}

// Save newly imported accounts to the local sessions directory
async function saveImportedAccountsToLocal(details, uploadedFiles = []) {
  const safeDetails = Array.isArray(details) ? details : []
  let savedCount = 0
  let failedCount = 0
  for (const detail of safeDetails) {
    if (detail.success && detail.id) {
      try {
        const account = await accountsApi.getOne(detail.id)

        // Find original uploaded files matching this phone number
        const sessionFile = uploadedFiles.find(f =>
          f.name.includes(detail.phone) && f.name.endsWith('.session')
        )
        const jsonFile = uploadedFiles.find(f =>
          f.name.includes(detail.phone) && f.name.endsWith('.json')
        )

        // Read binary session content if available
        let sessionContent = null
        if (sessionFile) {
          sessionContent = await readFileAsArrayBuffer(sessionFile)
        }

        // Parse JSON config if available
        let jsonConfig = null
        if (jsonFile) {
          try {
            const text = await readFileAsText(jsonFile)
            jsonConfig = JSON.parse(text)
          } catch (err) {
            console.warn(`⚠️ JSON 解析失败 (${detail.phone}):`, err)
          }
        }

        const result = await window.electron.ipcRenderer.invoke('save-session-to-local', {
          account,
          sessionContent,
          jsonConfig,
        })
        if (result && result.success) {
          savedCount++
        } else {
          failedCount++
        }
      } catch (err) {
        failedCount++
        console.error(`保存本地 session 失败 (${detail.phone}):`, err)
      }
    }
  }
  if (savedCount > 0) {
    ElMessage.success(`已保存 ${savedCount} 个账号到本地 sessions 目录`, { duration: 3000 })
  }
  if (failedCount > 0) {
    ElMessage.warning(`${failedCount} 个账号保存到本地失败，请检查 sessions 目录权限`)
  }
}

// Helper: read file as ArrayBuffer
function readFileAsArrayBuffer(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target.result)
    reader.onerror = reject
    reader.readAsArrayBuffer(file)
  })
}

// Helper: read file as text
function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target.result)
    reader.onerror = reject
    reader.readAsText(file)
  })
}

// Session 导入
async function importSession() {
  if (!sessionForm.value.session_string) {
    ElMessage.warning('请输入 Session 字符串')
    return
  }

  importing.value = true
  logger.task('导入', 'Session 字符串导入开始', { phone: sessionForm.value.phone || '未填写' })
  try {
    if (isElectron.value) {
      // Electron: write config + session string directly to local sessions/未检查/
      const phone = sessionForm.value.phone || `session_${Date.now()}`
      const config = {
        phone,
        app_id: sessionForm.value.api_id ? parseInt(sessionForm.value.api_id, 10) : null,
        app_hash: sessionForm.value.api_hash || null,
        twoFA: null,
        spamblock: 'unknown',
        session_file: phone,
        session_created_date: new Date().toISOString(),
      }
      const fileList = [
        { name: `${phone}.json`, buffer: Array.from(new TextEncoder().encode(JSON.stringify(config, null, 2))) },
        { name: `${phone}.session`, buffer: Array.from(new TextEncoder().encode(sessionForm.value.session_string)) },
      ]
      const result = await window.electron.ipcRenderer.invoke('import-files-locally', { fileList })
      const safeResult = (result && typeof result === 'object') ? result : { success: 0, failed: 0, details: [] }
      if (safeResult.success > 0) {
        logger.taskSuccess('导入', 'Session 导入成功（本地）', { phone })
        ElMessage.success('Session 导入成功')
        importResults.value.unshift({ filename: 'Session 字符串', phone, success: true, message: '导入成功' })
        sessionForm.value = { session_string: '', phone: '', api_id: '', api_hash: '' }
      } else {
        const msg = safeResult.details?.[0]?.message || '导入失败'
        logger.taskError('导入', 'Session 导入失败（本地）', msg)
        ElMessage.error(msg)
      }
    } else {
      // Non-Electron: use backend API
      const rawApiId = parseInt(sessionForm.value.api_id, 10)
      const payload = {
        session_string: sessionForm.value.session_string,
        phone: sessionForm.value.phone || '',
        api_id: sessionForm.value.api_id && !isNaN(rawApiId) ? rawApiId : null,
        api_hash: sessionForm.value.api_hash || null,
      }
      const result = await accountsApi.importSession(payload)
      if (result.success) {
        logger.taskSuccess('导入', 'Session 导入成功', result.account)
        ElMessage.success('Session 导入成功')
        importResults.value.unshift({
          filename: 'Session 字符串',
          phone: sessionForm.value.phone,
          success: true,
          message: '导入成功',
        })
        // Save to local sessions directory
        if (isElectron.value && result.account) {
          try {
            const fullAccount = await accountsApi.getOne(result.account.id)
            await window.electron.ipcRenderer.invoke('save-session-to-local', { account: fullAccount })
          } catch (err) {
            console.error('保存本地 session 失败:', err)
          }
        }
        sessionForm.value = { session_string: '', phone: '', api_id: '', api_hash: '' }
      } else {
        logger.taskError('导入', 'Session 导入失败', result.message)
        ElMessage.error(result.message || '导入失败')
      }
    }
  } catch (err) {
    logger.taskError('导入', 'Session 导入异常', err.message)
    ElMessage.error('导入失败：' + err.message)
  } finally {
    importing.value = false
  }
}

// 手动添加
async function addManual() {
  if (!manualForm.value.phone || !manualForm.value.api_id || !manualForm.value.api_hash) {
    ElMessage.warning('请填写完整信息')
    return
  }

  importing.value = true
  try {
    await accountsApi.create(manualForm.value)
    ElMessage.success('账号已添加')
    importResults.value.unshift({
      filename: '手动输入',
      phone: manualForm.value.phone,
      success: true,
      message: '添加成功',
    })
    manualForm.value = { phone: '', api_id: '', api_hash: '', proxy_id: null }
  } catch (err) {
    ElMessage.error('添加失败：' + err.message)
  } finally {
    importing.value = false
  }
}

// 下载模板
function downloadTemplate() {
  logger.task('导入', '下载模板')
  const template = {
    phone: '+1234567890',
    api_id: 12345,
    api_hash: 'your_api_hash_here',
  }
  const blob = new Blob([JSON.stringify(template, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'account_template.json'
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('模板已下载')
}
</script>

<style scoped>
.import-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.import-left,
.import-right {
  background: #252938;
  border-radius: 8px;
  padding: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--color-text);
}

.upload-area {
  border: 2px dashed #4a5568;
  border-radius: 8px;
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #1e2330;
}

.upload-area:hover,
.upload-area.is-dragover {
  border-color: #409eff;
  background: #252938;
}

.upload-text {
  font-size: 16px;
  margin: 16px 0 8px;
  color: var(--color-text);
}

.upload-hint {
  font-size: 14px;
  color: #909399;
  margin: 4px 0;
}

.upload-warning {
  font-size: 12px;
  color: #f56c6c;
  margin-top: 8px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.empty-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 0;
  color: #909399;
}

.result-summary {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.import-instructions {
  font-size: 14px;
  color: #909399;
  line-height: 1.8;
  padding-left: 20px;
}

.import-instructions code {
  background: #1e2330;
  padding: 2px 6px;
  border-radius: 4px;
  color: #409eff;
  font-size: 12px;
}
</style>
