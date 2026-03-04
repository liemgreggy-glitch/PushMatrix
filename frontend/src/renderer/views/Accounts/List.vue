<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">账号列表</span>
      <div class="header-actions">
        <el-input
          v-model="searchQuery"
          placeholder="搜索手机号/用户名"
          prefix-icon="Search"
          clearable
          style="width: 220px;"
          @input="handleSearch"
        />
        <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 120px;" @change="handleSearch">
          <el-option label="在线" value="online" />
          <el-option label="离线" value="offline" />
          <el-option label="冻结" value="frozen" />
          <el-option label="受限" value="spam" />
        </el-select>
        <el-button type="primary" icon="Plus" @click="showAddDialog = true">添加账号</el-button>
        <el-button icon="Upload" @click="$router.push('/accounts/import')">批量导入</el-button>
      </div>
    </div>

    <ActionBar
      :selected-count="selectedIds.length"
      :total="accounts.length"
      @clear-selection="clearSelection"
      @action="handleBulkAction"
    />

    <AccountTable
      :accounts="filteredAccounts"
      :loading="loading"
      @selection-change="handleSelectionChange"
      @row-action="handleRowAction"
    />

    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :total="total"
      layout="total, sizes, prev, pager, next"
      :page-sizes="[20, 50, 100]"
    />

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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import ActionBar from '../../components/Layout/ActionBar.vue'
import AccountTable from '../../components/AccountTable.vue'
import { accountsApi } from '../../api/index.js'

const accounts = ref([])
const loading = ref(false)
const total = ref(0)
const selectedIds = ref([])
const searchQuery = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const showAddDialog = ref(false)
const newAccount = ref({ phone: '', session_string: '', api_id: null, api_hash: '', proxy_id: null })

const filteredAccounts = computed(() => {
  let list = accounts.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(a => a.phone.includes(q) || (a.username || '').toLowerCase().includes(q))
  }
  if (filterStatus.value) {
    list = list.filter(a => a.status === filterStatus.value)
  }
  return list
})

async function loadAccounts() {
  loading.value = true
  try {
    const data = await accountsApi.getList()
    accounts.value = data
    total.value = data.length
  } catch (err) {
    ElMessage.error('加载账号列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {}

function handleSelectionChange(selection) {
  selectedIds.value = selection.map(a => a.id)
}

function clearSelection() {
  selectedIds.value = []
}

async function handleBulkAction(action) {
  if (!selectedIds.value.length) return
  try {
    await accountsApi.bulkAction({ action_type: action, account_ids: selectedIds.value })
    ElMessage.success(`操作 "${action}" 已执行`)
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

async function handleRowAction(action, row) {
  if (action === 'delete') {
    try {
      await accountsApi.delete(row.id)
      accounts.value = accounts.value.filter(a => a.id !== row.id)
      ElMessage.success('账号已删除')
    } catch (err) {
      ElMessage.error('删除失败')
    }
  } else {
    ElMessage.info(`操作: ${action} - 账号: ${row.phone}`)
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

onMounted(loadAccounts)
</script>
