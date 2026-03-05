<template>
  <div class="page-container accounts-container">
    <div class="page-header">
      <span class="page-title">账号列表</span>
      <div class="header-actions">
        <el-button icon="Upload" @click="$router.push('/accounts/import')">导入账号</el-button>
        <el-button icon="Download" @click="handleExport">导出账号</el-button>
        <el-button v-if="isElectron" icon="Folder" @click="handleOpenSessionsFolder">打开 Sessions 目录</el-button>
      </div>
    </div>

    <!-- Sessions directory path hint -->
    <div v-if="isElectron && sessionsDir" class="sessions-dir-hint">
      <el-icon><Folder /></el-icon>
      <span>{{ sessionsDir }}</span>
    </div>

    <!-- Statistics Cards -->
    <div class="stats-grid">
      <StatCard
        v-for="stat in stats"
        :key="stat.key"
        :value="stat.value"
        :label="stat.label"
        :color="stat.color"
      />
    </div>

    <!-- Toolbar -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button size="small" @click="handleSelectChecked" icon="Check">选中</el-button>
        <el-button size="small" @click="handleSelectAll" icon="Select">全选</el-button>
        <el-button size="small" @click="handleSelectUnchecked" icon="Minus">未选中</el-button>
        <el-button size="small" @click="handleCancelSelect" icon="Close">取消选中</el-button>
        <el-divider direction="vertical" />
        <el-button size="small" @click="handleRefresh" icon="Refresh">刷新</el-button>
        <el-button size="small" type="danger" icon="Delete" @click="handleBatchDelete">删除</el-button>
      </div>
    </div>

    <!-- Account Table -->
    <el-table
      ref="tableRef"
      v-loading="loading"
      :data="accounts"
      @selection-change="handleSelectionChange"
      class="account-table"
      row-key="id"
    >
      <el-table-column type="selection" width="50" />
      <el-table-column label="手机号" prop="phone" width="150" />
      <el-table-column label="地理" width="140">
        <template #default="{ row }">
          <span>{{ row.country_flag }} {{ row.country_name }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="160">
        <template #default="{ row }">
          <div style="display: flex; flex-direction: column; gap: 2px;">
            <el-tag
              size="small"
              :style="{ backgroundColor: getStatusColor(row.restriction_status || row.status) + '22', color: getStatusColor(row.restriction_status || row.status), borderColor: getStatusColor(row.restriction_status || row.status) + '44' }"
            >
              {{ getStatusText(row.restriction_status || row.status) }}
            </el-tag>
            <span v-if="row.restriction_status === 'SPAM_TEMP' && row.spam_until" style="font-size: 11px; color: #f97316;">
              至 {{ new Date(row.spam_until).toLocaleDateString('zh-CN') }}
            </span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="注册时间" width="120">
        <template #default="{ row }">
          <span>{{ formatRegistered(row.registered_months) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="名称" prop="first_name" width="150" />
      <el-table-column label="用户名" width="150">
        <template #default="{ row }">
          <span class="text-muted">{{ row.username ? `@${row.username}` : '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="2FA" prop="two_fa" width="100">
        <template #default="{ row }">
          <span>{{ row.two_fa || '-' }}</span>
        </template>
      </el-table-column>
    </el-table>

    <!-- Fixed Bottom Action Bar -->
    <div v-if="selectedAccounts.length > 0" class="fixed-action-bar">
      <div class="action-bar-content">
        <span class="selection-info">
          已选择: {{ selectedAccounts.length }} / {{ accounts.length }} 个账号
        </span>
        <div class="action-buttons">
          <el-dropdown trigger="click">
            <el-button>
              移动账号 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>移动到分组 A</el-dropdown-item>
                <el-dropdown-item>移动到分组 B</el-dropdown-item>
                <el-dropdown-item divided>创建新分组...</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <ActionMenu :selected-accounts="selectedAccounts" @action="handleAction" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Folder } from '@element-plus/icons-vue'
import StatCard from '../../components/StatCard.vue'
import ActionMenu from '../../components/ActionMenu.vue'
import { accountsApi } from '../../api/index.js'
import { logCheck, logCheckResult, logCheckStats } from '../../utils/checkLogger.js'

const tableRef = ref(null)
const accounts = ref([])
const loading = ref(false)
const selectedAccounts = ref([])
const sessionsDir = ref('')

const isElectron = computed(() => {
  return typeof window !== 'undefined' && window.electron !== undefined
})

const stats = ref([
  { key: 'total',        value: 0, label: '账号总数',     color: '#10b981' },
  { key: 'idle',         value: 0, label: '未工作',       color: '#6b7280' },
  { key: 'unlimited',    value: 0, label: '无限制',       color: '#3b82f6' },
  { key: 'spam',         value: 0, label: '垃圾邮件',     color: '#ef4444' },
  { key: 'frozen',       value: 0, label: '冻结',         color: '#f59e0b' },
  { key: 'banned',       value: 0, label: '封禁',         color: '#dc2626' },
  { key: 'disconnected', value: 0, label: '未连接',       color: '#eab308' },
])

const STATUS_CONFIG = {
  // 旧 status 字段值（兼容）
  unlimited:    { text: '无限制',       color: '#10b981' },
  frozen:       { text: '冻结',         color: '#f59e0b' },
  banned:       { text: '封禁',         color: '#dc2626' },
  disconnected: { text: '未连接',       color: '#eab308' },
  idle:         { text: '未工作',       color: '#6b7280' },
  spam:         { text: '垃圾邮件',     color: '#ef4444' },
  // 新 restriction_status 字段值
  UNRESTRICTED:   { text: '✅ 无限制',         color: '#10b981' },
  SPAM_PERMANENT: { text: '⚠️ 永久垃圾邮件',   color: '#ef4444' },
  SPAM_TEMP:      { text: '⏳ 临时限制',        color: '#f97316' },
  FROZEN:         { text: '❄️ 冻结',           color: '#f59e0b' },
  BANNED:         { text: '🚫 封禁',           color: '#dc2626' },
  UNKNOWN_ERROR:  { text: '❓ 未知错误',        color: '#6b7280' },
}

function getStatusColor(status) {
  return STATUS_CONFIG[status]?.color || '#6b7280'
}

function getStatusText(status) {
  return STATUS_CONFIG[status]?.text || status || '未知'
}

function formatRegistered(months) {
  if (!months && months !== 0) return '-'
  if (months >= 12) {
    const years = Math.floor(months / 12)
    return `${years}年`
  }
  return `${months}个月`
}

function handleSelectionChange(selection) {
  selectedAccounts.value = selection
}

function handleSelectChecked() {
  const checkedCount = selectedAccounts.value.length
  if (checkedCount === 0) {
    ElMessage.info('当前没有已选中的账号')
  } else {
    ElMessage.success(`已选中 ${checkedCount} 个账号`)
  }
}

function handleSelectAll() {
  tableRef.value?.toggleAllSelection()
}

function handleSelectUnchecked() {
  const currentSelectedIds = new Set(selectedAccounts.value.map(acc => acc.id))
  tableRef.value?.clearSelection()
  nextTick(() => {
    accounts.value.forEach(acc => {
      if (!currentSelectedIds.has(acc.id)) {
        tableRef.value?.toggleRowSelection(acc, true)
      }
    })
  })
}

function handleCancelSelect() {
  tableRef.value?.clearSelection()
}

async function handleRefresh() {
  await loadAccounts()
}

async function handleOpenSessionsFolder() {
  if (!isElectron.value) return
  try {
    await window.electron.ipcRenderer.invoke('open-sessions-folder')
  } catch (err) {
    ElMessage.error('打开目录失败')
  }
}

async function handleExport() {
  try {
    const data = await accountsApi.export({ format: 'json' })
    const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `accounts_export_${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success(`已导出 ${data.count} 个账号`)
  } catch (err) {
    ElMessage.error('导出失败: ' + err.message)
  }
}

async function handleBatchDelete() {
  if (!selectedAccounts.value.length) {
    ElMessage.warning('请先选择需要删除的账号')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedAccounts.value.length} 个账号吗？此操作不可撤销。`,
      '批量删除确认',
      { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }
    )

    if (isElectron.value) {
      // Electron: delete local files only; the fs.watch listener will trigger a list refresh
      let deletedCount = 0
      let failedCount = 0
      for (const account of selectedAccounts.value) {
        try {
          await window.electron.ipcRenderer.invoke('delete-session', {
            phone: account.phone,
            restrictionStatus: account.restriction_status,
          })
          deletedCount++
        } catch (err) {
          failedCount++
          console.error(`删除本地文件失败 (${account.phone}):`, err)
        }
      }
      if (failedCount > 0) {
        ElMessage.warning(`${failedCount} 个账号删除失败`)
      } else {
        ElMessage.success(`已删除 ${deletedCount} 个账号`)
      }
    } else {
      // Non-Electron: call server API
      const ids = selectedAccounts.value.map(a => a.id)
      const result = await accountsApi.bulkDelete({ account_ids: ids })
      ElMessage.success(`已删除 ${result.deleted} 个账号`)
      await loadAccounts()
    }
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败: ' + (err.message || '未知错误'))
    }
  }
}

// Simple concurrency limiter using native Promises
function createConcurrencyLimit(concurrency) {
  let active = 0
  const queue = []
  function run() {
    if (active >= concurrency || queue.length === 0) return
    active++
    const { fn, resolve, reject } = queue.shift()
    fn().then(resolve, reject).finally(() => {
      active--
      run()
    })
  }
  return (fn) => new Promise((resolve, reject) => {
    queue.push({ fn, resolve, reject })
    run()
  })
}

async function handleBatchCheckSpam(accountsToCheck) {
  if (!accountsToCheck.length) {
    ElMessage.warning('请先选择账号')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定检查选中的 ${accountsToCheck.length} 个账号的限制状态吗？\n\n此操作将登录每个账号并向 @SpamBot 发送消息。`,
      '批量检查确认',
      { confirmButtonText: '开始检查', cancelButtonText: '取消', type: 'info' }
    )
  } catch {
    // User cancelled – no action needed
    return
  }

  const concurrency = parseInt(localStorage.getItem('check_concurrency') || '100', 10)
  const delay = parseInt(localStorage.getItem('check_delay_ms') || '500', 10)
  const total = accountsToCheck.length

  logCheck('='.repeat(70))
  logCheck(`开始检查 ${total} 个账号，并发数: ${concurrency}`)
  logCheck('='.repeat(70))

  const statusCounts = { UNRESTRICTED: 0, SPAM: 0, FROZEN: 0, BANNED: 0, UNKNOWN: 0, UNAUTHORIZED: 0 }
  const limit = createConcurrencyLimit(concurrency)
  let completed = 0

  const tasks = accountsToCheck.map((account, index) =>
    limit(async () => {
      if (delay > 0) {
        await new Promise(r => setTimeout(r, delay))
      }
      try {
        logCheck(`[${index + 1}/${total}] ${account.phone} → 正在连接...`)
        const oldStatus = account.restriction_status
        const result = await accountsApi.checkRestrictionStatus(account.id)
        completed++
        const status = result.restriction_status || 'UNKNOWN'
        statusCounts[status] = (statusCounts[status] || 0) + 1
        logCheckResult(index + 1, total, account.phone, status)

        // Move local session files if restriction status changed
        if (isElectron.value && oldStatus !== status) {
          try {
            await window.electron.ipcRenderer.invoke('move-session', {
              phone: account.phone,
              oldStatus,
              newStatus: status,
            })
            // Update JSON config with latest account data
            const updatedAccount = await accountsApi.getOne(account.id)
            await window.electron.ipcRenderer.invoke('update-session-config', {
              account: updatedAccount,
            })
          } catch (localErr) {
            console.error(`本地文件操作失败 (${account.phone}):`, localErr)
          }
        }

        if (completed % 10 === 0 || completed === total) {
          logCheck(
            `进度: ${completed}/${total} | ✅ ${statusCounts.UNRESTRICTED} ⚠️ ${statusCounts.SPAM} ❄️ ${statusCounts.FROZEN} 🚫 ${statusCounts.BANNED} ❌ ${statusCounts.UNAUTHORIZED} ❓ ${statusCounts.UNKNOWN}`
          )
        }
        return result
      } catch (err) {
        completed++
        statusCounts.UNKNOWN = (statusCounts.UNKNOWN || 0) + 1
        logCheck(`[${index + 1}/${total}] ${account.phone} → 错误: ${err.message}`)
        logCheckResult(index + 1, total, account.phone, 'ERROR')
        return { restriction_status: 'UNKNOWN' }
      }
    })
  )

  await Promise.all(tasks)

  logCheck('='.repeat(70))
  logCheckStats({
    unrestricted: statusCounts.UNRESTRICTED,
    spam: statusCounts.SPAM,
    frozen: statusCounts.FROZEN,
    banned: statusCounts.BANNED,
    unauthorized: statusCounts.UNAUTHORIZED,
    unknown: statusCounts.UNKNOWN,
  })
  logCheck('='.repeat(70))

  await loadAccounts()
  ElMessage.success(`检查完成！无限制: ${statusCounts.UNRESTRICTED}, 受限: ${statusCounts.SPAM + statusCounts.FROZEN + statusCounts.BANNED}`)
}

async function handleAction(command, actionAccounts) {
  const ids = actionAccounts.map(a => a.id)
  try {
    if (command === 'check-spam') {
      await handleBatchCheckSpam(actionAccounts)
    } else {
      await accountsApi.bulkAction({ action_type: command, account_ids: ids })
      ElMessage.success('操作已执行')
      await loadAccounts()
    }
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

async function loadAccounts() {
  loading.value = true
  try {
    if (isElectron.value) {
      // Electron: read account list directly from local session files
      const localAccounts = await window.electron.ipcRenderer.invoke('scan-local-accounts')
      const safeAccounts = Array.isArray(localAccounts) ? localAccounts : []
      accounts.value = safeAccounts
      // Recalculate statistics
      const s = { total: 0, idle: 0, unlimited: 0, spam: 0, frozen: 0, banned: 0, disconnected: 0 }
      s.total = safeAccounts.length
      for (const acc of safeAccounts) {
        const rs = acc.restriction_status
        if (rs === 'UNRESTRICTED') s.unlimited++
        else if (rs === 'SPAM' || rs === 'SPAM_PERMANENT' || rs === 'SPAM_TEMP') s.spam++
        else if (rs === 'FROZEN') s.frozen++
        else if (rs === 'BANNED') s.banned++
        else if (rs === null) s.idle++
        else s.disconnected++
      }
      stats.value.forEach(stat => {
        if (stat.key in s) stat.value = s[stat.key]
      })
    } else {
      // Non-Electron: use server API
      const data = await accountsApi.getList()
      // Guard: ensure accounts is always an array even when data is undefined
      const list = Array.isArray(data?.items)
        ? data.items
        : Array.isArray(data?.accounts)
          ? data.accounts
          : Array.isArray(data)
            ? data
            : []
      accounts.value = list
      const s = data?.stats
      if (s) {
        stats.value.forEach(stat => {
          if (stat.key in s) stat.value = s[stat.key]
        })
      }
    }
  } catch (err) {
    accounts.value = []   
    ElMessage.error('加载账号列表失败: ' + (err.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadAccounts()
  if (isElectron.value) {
    try {
      sessionsDir.value = await window.electron.ipcRenderer.invoke('get-sessions-dir')
      // Watch sessions folder and auto-refresh when files change
      await window.electron.ipcRenderer.invoke('watch-sessions')
      window.electron.ipcRenderer.on('sessions-changed', () => {
        loadAccounts()
      })
    } catch (err) {
      console.error('初始化失败:', err)
    }
  }
})
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.accounts-container {
  padding-bottom: 80px;
}

.toolbar {
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #252938;
  border-radius: 8px;
}

.toolbar-left {
  display: flex;
  gap: 8px;
  align-items: center;
}

.account-table {
  background: #252938;
  border-radius: 8px;
  margin-bottom: 16px;
}

.fixed-action-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: linear-gradient(to top, rgba(17, 24, 39, 0.98), rgba(17, 24, 39, 0.95));
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: 16px 24px;
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.3);
}

.action-bar-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.selection-info {
  color: #9ca3af;
  font-size: 14px;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.text-muted {
  color: var(--color-text-muted);
}

.sessions-dir-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 12px;
  padding: 6px 12px;
  background: #1a1d2e;
  border-radius: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
