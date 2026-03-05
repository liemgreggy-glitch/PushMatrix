<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">账号列表</span>
      <div class="header-actions">
        <el-button type="primary" icon="Refresh" @click="handleBatchCheck" :loading="checking">
          批量检查
        </el-button>
        <el-button icon="Clock" @click="showScheduleDialog = true">定时检查</el-button>
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
        <el-button size="small" icon="Plus" @click="showAddDialog = true">添加</el-button>
        <el-button size="small" icon="Upload" @click="$router.push('/accounts/import')">导入</el-button>
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

    <!-- Add Account Dialog -->
    <el-dialog v-model="showAddDialog" title="添加账号" width="480px">
      <el-form :model="newAccount" label-width="100px">
        <el-form-item label="手机号" required>
          <el-input v-model="newAccount.phone" placeholder="+1234567890" />
        </el-form-item>
        <el-form-item label="Session">
          <el-input v-model="newAccount.session_string" type="textarea" :rows="3" placeholder="Session 字符串（可选）" />
        </el-form-item>
        <el-form-item label="API ID">
          <el-input v-model="newAccount.api_id" placeholder="Telegram API ID" />
        </el-form-item>
        <el-form-item label="API Hash">
          <el-input v-model="newAccount.api_hash" placeholder="Telegram API Hash" />
        </el-form-item>
        <el-form-item label="代理">
          <el-select v-model="newAccount.proxy_id" clearable placeholder="选择代理（可选）" style="width: 100%;">
            <el-option label="无代理" :value="null" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="submitAccount">添加</el-button>
      </template>
    </el-dialog>

    <!-- Schedule Dialog -->
    <el-dialog v-model="showScheduleDialog" title="设置定时检查" width="400px">
      <el-form label-width="100px">
        <el-form-item label="检查频率">
          <el-select v-model="scheduleForm.cron" style="width: 100%;">
            <el-option label="每天 09:00" value="0 9 * * *" />
            <el-option label="每天 21:00" value="0 21 * * *" />
            <el-option label="每6小时" value="0 */6 * * *" />
            <el-option label="每12小时" value="0 */12 * * *" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showScheduleDialog = false">取消</el-button>
        <el-button type="primary" @click="saveSchedule">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import StatCard from '../../components/StatCard.vue'
import ActionMenu from '../../components/ActionMenu.vue'
import { accountsApi } from '../../api/index.js'

const tableRef = ref(null)
const accounts = ref([])
const loading = ref(false)
const checking = ref(false)
const selectedAccounts = ref([])
const showAddDialog = ref(false)
const showScheduleDialog = ref(false)
const scheduleForm = ref({ cron: '0 9 * * *' })
const newAccount = ref({ phone: '', session_string: '', api_id: null, api_hash: '', proxy_id: null })

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
  // 保持当前选中状态
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
  // 反选：选中所有未勾选的行，取消选中已勾选的行
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

async function handleBatchCheck() {
  if (!selectedAccounts.value.length) {
    ElMessage.warning('请先选择需要检查的账号')
    return
  }
  checking.value = true
  try {
    const ids = selectedAccounts.value.map(a => a.id)
    await accountsApi.bulkCheckSpam({ account_ids: ids })
    ElMessage.success('批量检查已完成')
    await loadAccounts()
  } catch (err) {
    ElMessage.error('检查失败')
  } finally {
    checking.value = false
  }
}

async function handleAction(command, accounts) {
  const ids = accounts.map(a => a.id)
  try {
    if (command === 'check-spam') {
      await accountsApi.bulkCheckSpam({ account_ids: ids })
      ElMessage.success('垃圾邮件检查已完成')
    } else {
      await accountsApi.bulkAction({ action_type: command, account_ids: ids })
      ElMessage.success(`操作已执行`)
    }
    await loadAccounts()
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

async function loadAccounts() {
  loading.value = true
  try {
    const data = await accountsApi.getList()
    if (data && data.accounts) {
      accounts.value = data.accounts
      const s = data.stats
      stats.value.forEach(stat => {
        if (s && stat.key in s) {
          stat.value = s[stat.key]
        }
      })
    } else {
      accounts.value = Array.isArray(data) ? data : []
    }
  } catch (err) {
    ElMessage.error('加载账号列表失败')
  } finally {
    loading.value = false
  }
}

async function submitAccount() {
  try {
    await accountsApi.create(newAccount.value)
    ElMessage.success('账号已添加')
    showAddDialog.value = false
    loadAccounts()
  } catch (err) {
    ElMessage.error('添加失败: ' + err.message)
  }
}

async function saveSchedule() {
  // TODO: 实现定时检查的实际保存逻辑
  ElMessage.success('定时检查已设置')
  showScheduleDialog.value = false
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
