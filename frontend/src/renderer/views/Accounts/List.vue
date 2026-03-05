<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">账号列表</span>
      <div class="header-actions">
        <el-button icon="Upload" @click="$router.push('/accounts/import')">导入账号</el-button>
        <el-button icon="Download" @click="handleExport">导出账号</el-button>
      </div>
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
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag
            size="small"
            :style="{ backgroundColor: getStatusColor(row.status) + '22', color: getStatusColor(row.status), borderColor: getStatusColor(row.status) + '44' }"
          >
            {{ getStatusText(row.status) }}
          </el-tag>
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

    <!-- Bottom Action Bar -->
    <div class="bottom-actions">
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
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import StatCard from '../../components/StatCard.vue'
import ActionMenu from '../../components/ActionMenu.vue'
import { accountsApi } from '../../api/index.js'

const tableRef = ref(null)
const accounts = ref([])
const loading = ref(false)
const selectedAccounts = ref([])

const stats = ref([
  { key: 'total', value: 0, label: '账号总数', color: '#10b981' },
  { key: 'idle', value: 0, label: '未工作', color: '#6b7280' },
  { key: 'unlimited', value: 0, label: '无限制', color: '#3b82f6' },
  { key: 'spam', value: 0, label: '垃圾邮件', color: '#ef4444' },
  { key: 'frozen', value: 0, label: '冻结', color: '#f59e0b' },
  { key: 'banned', value: 0, label: '封禁', color: '#dc2626' },
  { key: 'disconnected', value: 0, label: '未连接', color: '#eab308' },
])

const STATUS_CONFIG = {
  unlimited: { text: '无限制', color: '#10b981' },
  spam: { text: '垃圾邮件', color: '#ef4444' },
  frozen: { text: '冻结', color: '#f59e0b' },
  banned: { text: '封禁', color: '#dc2626' },
  disconnected: { text: '未连接', color: '#eab308' },
  idle: { text: '未工作', color: '#6b7280' },
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
    const ids = selectedAccounts.value.map(a => a.id)
    const result = await accountsApi.bulkDelete({ account_ids: ids })
    ElMessage.success(`已删除 ${result.deleted} 个账号`)
    await loadAccounts()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败: ' + err.message)
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
  const concurrency = parseInt(localStorage.getItem('check_concurrency') || '100', 10)
  const delay = parseInt(localStorage.getItem('check_delay_ms') || '500', 10)
  const total = accountsToCheck.length

  console.log(`📋 [检查限制] 开始检查 ${total} 个账号，并发数: ${concurrency}`)

  const statusCounts = { unlimited: 0, spam: 0, frozen: 0, banned: 0, disconnected: 0, idle: 0 }
  const limit = createConcurrencyLimit(concurrency)
  let completed = 0

  const STATUS_LABELS = {
    unlimited: '✅ 无限制',
    spam: '⚠️ 垃圾邮件限制',
    frozen: '❄️ 冻结',
    banned: '🚫 封禁',
    disconnected: '🔌 未连接',
    idle: '⏸️ 未工作',
  }

  const tasks = accountsToCheck.map(account =>
    limit(async () => {
      if (delay > 0) {
        await new Promise(r => setTimeout(r, delay))
      }
      try {
        const result = await accountsApi.checkSpamStatusSingle(account.id)
        completed++
        const status = result.status || 'idle'
        statusCounts[status] = (statusCounts[status] || 0) + 1
        const label = STATUS_LABELS[status] || status
        console.log(`${label.split(' ')[0]} [检查限制] [${completed}/${total}] ${account.phone} → ${label}`)
        return result
      } catch (err) {
        completed++
        statusCounts.disconnected = (statusCounts.disconnected || 0) + 1
        console.log(`❌ [检查限制] [${completed}/${total}] ${account.phone} → 错误: ${err.message}`)
        return { status: 'disconnected' }
      }
    })
  )

  await Promise.all(tasks)

  console.log('📋 [检查限制] =======================================')
  console.log('✅ [检查限制] 检查完成！统计结果：')
  if (statusCounts.unlimited) console.log(`📋 [检查限制] ✅ 无限制: ${statusCounts.unlimited} 个`)
  if (statusCounts.spam) console.log(`📋 [检查限制] ⚠️ 垃圾邮件限制: ${statusCounts.spam} 个`)
  if (statusCounts.frozen) console.log(`📋 [检查限制] ❄️ 冻结: ${statusCounts.frozen} 个`)
  if (statusCounts.banned) console.log(`📋 [检查限制] 🚫 封禁: ${statusCounts.banned} 个`)
  if (statusCounts.disconnected) console.log(`📋 [检查限制] 🔌 未连接/错误: ${statusCounts.disconnected} 个`)
  console.log('📋 [检查限制] =======================================')

  await loadAccounts()
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
    const data = await accountsApi.getList()
    accounts.value = data.items || data.accounts || (Array.isArray(data) ? data : [])
    const s = data.stats
    if (s) {
      stats.value.forEach(stat => {
        if (stat.key in s) {
          stat.value = s[stat.key]
        }
      })
    }
  } catch (err) {
    ElMessage.error('加载账号列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadAccounts)
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
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

.bottom-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px;
  background: #252938;
  border-radius: 8px;
}

.text-muted {
  color: var(--color-text-muted);
}
</style>
