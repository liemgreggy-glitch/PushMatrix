<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">账号分组</span>
      <el-button type="primary" icon="Plus" @click="showCreateDialog = true">新建分组</el-button>
    </div>

    <el-row :gutter="16">
      <el-col v-for="group in groups" :key="group.id" :span="8">
        <el-card class="group-card">
          <div class="group-header">
            <div class="group-info">
              <el-icon size="20" color="#409EFF"><FolderOpened /></el-icon>
              <span class="group-name">{{ group.name }}</span>
            </div>
            <div class="group-actions">
              <el-button circle icon="Edit" size="small" @click="editGroup(group)" />
              <el-button circle icon="Delete" size="small" type="danger" @click="deleteGroup(group.id)" />
            </div>
          </div>
          <p class="group-desc">{{ group.description || '暂无描述' }}</p>
          <div class="group-stats">
            <el-tag size="small">{{ groupAccountCount(group.id) }} 个账号</el-tag>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <div class="add-group-card" @click="showCreateDialog = true">
          <el-icon size="32" color="#409EFF"><Plus /></el-icon>
          <span>新建分组</span>
        </div>
      </el-col>
    </el-row>

    <el-dialog v-model="showCreateDialog" :title="editingGroup ? '编辑分组' : '新建分组'" width="400px">
      <el-form :model="groupForm" label-width="80px">
        <el-form-item label="分组名称" required>
          <el-input v-model="groupForm.name" placeholder="输入分组名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="groupForm.description" type="textarea" :rows="2" placeholder="描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="submitGroup">
          {{ editingGroup ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { accountsApi } from '../../api/index.js'

const groups = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const editingGroup = ref(null)
const groupForm = ref({ name: '', description: '' })

function groupAccountCount(groupId) {
  return 0 // TODO: count from accounts
}

function editGroup(group) {
  editingGroup.value = group
  groupForm.value = { name: group.name, description: group.description || '' }
  showCreateDialog.value = true
}

async function deleteGroup(id) {
  await ElMessageBox.confirm('确定删除该分组吗？', '删除确认', { type: 'warning' })
  try {
    await accountsApi.deleteGroup(id)
    groups.value = groups.value.filter(g => g.id !== id)
    ElMessage.success('分组已删除')
  } catch (err) {
    ElMessage.error('删除失败')
  }
}

async function submitGroup() {
  try {
    if (editingGroup.value) {
      await accountsApi.updateGroup(editingGroup.value.id, groupForm.value)
      const idx = groups.value.findIndex(g => g.id === editingGroup.value.id)
      if (idx !== -1) groups.value[idx] = { ...groups.value[idx], ...groupForm.value }
      ElMessage.success('分组已更新')
    } else {
      const newGroup = await accountsApi.createGroup(groupForm.value)
      groups.value.push(newGroup)
      ElMessage.success('分组已创建')
    }
    showCreateDialog.value = false
    editingGroup.value = null
    groupForm.value = { name: '', description: '' }
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

async function loadGroups() {
  loading.value = true
  try {
    groups.value = await accountsApi.getGroups()
  } catch (err) {
    ElMessage.error('加载分组失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadGroups)
</script>

<style scoped>
.group-card {
  margin-bottom: 0;
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.group-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.group-name {
  font-size: 16px;
  font-weight: 600;
}

.group-actions {
  display: flex;
  gap: 6px;
}

.group-desc {
  font-size: 13px;
  color: var(--color-text-muted);
  margin-bottom: 12px;
}

.group-stats {
  display: flex;
  gap: 8px;
}

.add-group-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 120px;
  border: 2px dashed var(--color-border);
  border-radius: var(--border-radius);
  cursor: pointer;
  color: var(--color-text-muted);
  transition: all 0.2s;
}

.add-group-card:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
</style>
