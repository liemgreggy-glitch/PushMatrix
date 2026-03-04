<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">代理管理</span>
      <div class="header-actions">
        <el-button type="primary" icon="Plus" @click="showAddDialog = true">添加代理</el-button>
        <el-button icon="Upload" @click="showImportDialog = true">批量导入</el-button>
        <el-button icon="Link" @click="autoAssign">自动分配</el-button>
      </div>
    </div>

    <el-table v-loading="loading" :data="proxies" style="width: 100%">
      <el-table-column label="类型" prop="proxy_type" width="80">
        <template #default="{ row }">
          <el-tag size="small" :type="row.proxy_type === 'socks5' ? 'primary' : 'success'">
            {{ row.proxy_type.toUpperCase() }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="地址" min-width="180">
        <template #default="{ row }">
          <span>{{ row.host }}:{{ row.port }}</span>
        </template>
      </el-table-column>
      <el-table-column label="认证" min-width="120">
        <template #default="{ row }">
          <span class="text-muted">{{ row.username ? `${row.username}:***` : '无认证' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="国家" prop="country" width="80">
        <template #default="{ row }">
          <span>{{ row.country || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small">
            {{ row.status === 'active' ? '正常' : row.status === 'error' ? '错误' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="响应时间" width="100">
        <template #default="{ row }">
          <span :class="responseClass(row.response_time)">
            {{ row.response_time ? `${row.response_time}ms` : '-' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" icon="Connection" @click="testProxy(row.id)">测试</el-button>
          <el-button size="small" icon="Edit" @click="editProxy(row)" />
          <el-button size="small" icon="Delete" type="danger" @click="deleteProxy(row.id)" />
        </template>
      </el-table-column>
    </el-table>

    <!-- Add/Edit Dialog -->
    <el-dialog v-model="showAddDialog" :title="editingProxy ? '编辑代理' : '添加代理'" width="440px">
      <el-form :model="proxyForm" label-width="80px">
        <el-form-item label="类型" required>
          <el-select v-model="proxyForm.proxy_type" style="width: 100%;">
            <el-option label="SOCKS5" value="socks5" />
            <el-option label="HTTP" value="http" />
          </el-select>
        </el-form-item>
        <el-form-item label="地址" required>
          <el-input v-model="proxyForm.host" placeholder="proxy.example.com" />
        </el-form-item>
        <el-form-item label="端口" required>
          <el-input-number v-model="proxyForm.port" :min="1" :max="65535" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="proxyForm.username" placeholder="可选" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="proxyForm.password" type="password" placeholder="可选" show-password />
        </el-form-item>
        <el-form-item label="国家代码">
          <el-input v-model="proxyForm.country" placeholder="US/CN/DE..." maxlength="5" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="submitProxy">{{ editingProxy ? '保存' : '添加' }}</el-button>
      </template>
    </el-dialog>

    <!-- Import Dialog -->
    <el-dialog v-model="showImportDialog" title="批量导入代理" width="480px">
      <el-input
        v-model="importText"
        type="textarea"
        :rows="10"
        placeholder="每行一个代理，格式: socks5://user:pass@host:port 或 host:port"
      />
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" @click="submitImport">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { proxiesApi } from '../api/index.js'

const proxies = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const showImportDialog = ref(false)
const editingProxy = ref(null)
const importText = ref('')
const proxyForm = ref({ proxy_type: 'socks5', host: '', port: 1080, username: '', password: '', country: '' })

function responseClass(ms) {
  if (!ms) return 'text-muted'
  if (ms < 200) return 'text-success'
  if (ms < 500) return 'text-warning'
  return 'text-danger'
}

function editProxy(proxy) {
  editingProxy.value = proxy
  proxyForm.value = { ...proxy }
  showAddDialog.value = true
}

async function testProxy(id) {
  try {
    const result = await proxiesApi.test(id)
    ElMessage.success(`代理测试成功，响应时间: ${result.response_time}ms`)
    const proxy = proxies.value.find(p => p.id === id)
    if (proxy) proxy.response_time = result.response_time
  } catch (err) {
    ElMessage.error('代理测试失败')
  }
}

async function deleteProxy(id) {
  await ElMessageBox.confirm('确定删除该代理吗？', '删除确认', { type: 'warning' })
  try {
    await proxiesApi.delete(id)
    proxies.value = proxies.value.filter(p => p.id !== id)
    ElMessage.success('代理已删除')
  } catch (err) {
    ElMessage.error('删除失败')
  }
}

async function submitProxy() {
  try {
    if (editingProxy.value) {
      await proxiesApi.update(editingProxy.value.id, proxyForm.value)
      ElMessage.success('代理已更新')
    } else {
      const newProxy = await proxiesApi.create(proxyForm.value)
      proxies.value.push(newProxy)
      ElMessage.success('代理已添加')
    }
    showAddDialog.value = false
    editingProxy.value = null
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

async function submitImport() {
  ElMessage.info('批量导入功能即将可用')
  showImportDialog.value = false
}

async function autoAssign() {
  ElMessage.info('自动分配功能即将可用')
}

async function loadProxies() {
  loading.value = true
  try {
    proxies.value = await proxiesApi.getList()
  } catch (err) {
    ElMessage.error('加载代理列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadProxies)
</script>
