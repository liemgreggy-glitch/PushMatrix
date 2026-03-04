<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">批量拉人</span>
      <el-button type="primary" icon="Plus" @click="showCreateWizard = true">新建任务</el-button>
    </div>

    <div v-loading="loading">
      <TaskCard
        v-for="task in tasks"
        :key="task.id"
        :task="task"
        @start="(id) => updateStatus(id, 'running')"
        @pause="(id) => updateStatus(id, 'paused')"
        @stop="(id) => updateStatus(id, 'stopped')"
        @delete="deleteTask"
      />
      <el-empty v-if="tasks.length === 0" description="暂无拉人任务" />
    </div>

    <el-dialog v-model="showCreateWizard" title="新建拉人任务" width="640px" destroy-on-close>
      <el-steps :active="wizardStep" finish-status="success" style="margin-bottom: 24px;">
        <el-step title="操作账号" />
        <el-step title="目标群组" />
        <el-step title="用户来源" />
        <el-step title="设置参数" />
      </el-steps>

      <div class="step-content">
        <div v-if="wizardStep === 0">
          <p class="step-desc">选择执行拉人的账号</p>
          <el-checkbox-group v-model="newTask.account_ids">
            <el-checkbox v-for="acc in mockAccounts" :key="acc.id" :label="acc.id" style="display: block; margin-bottom: 8px;">
              {{ acc.phone }}
            </el-checkbox>
          </el-checkbox-group>
        </div>

        <div v-if="wizardStep === 1">
          <p class="step-desc">选择拉人目标群组</p>
          <el-select v-model="newTask.target_group" placeholder="选择群组" style="width: 100%;">
            <el-option v-for="g in groups" :key="g.id" :label="`${g.title} (${g.members} 成员)`" :value="g.id" />
          </el-select>
          <p v-if="newTask.target_group" class="permission-check">
            <el-icon color="#A6E3A1"><CircleCheck /></el-icon>
            权限已验证
          </p>
        </div>

        <div v-if="wizardStep === 2">
          <p class="step-desc">选择用户来源</p>
          <el-radio-group v-model="sourceType" style="display: flex; flex-direction: column; gap: 12px;">
            <el-radio label="group">从其他群组提取</el-radio>
            <el-radio label="import">导入用户列表</el-radio>
            <el-radio label="contacts">从联系人</el-radio>
          </el-radio-group>
          <div v-if="sourceType === 'group'" style="margin-top: 12px;">
            <el-select v-model="sourceGroup" placeholder="选择来源群组" style="width: 100%;">
              <el-option v-for="g in groups" :key="g.id" :label="g.title" :value="g.id" />
            </el-select>
          </div>
          <div v-if="sourceType === 'import'" style="margin-top: 12px;">
            <el-input v-model="userList" type="textarea" :rows="5" placeholder="每行一个用户名或ID" />
          </div>
        </div>

        <div v-if="wizardStep === 3">
          <p class="step-desc">配置参数</p>
          <el-form label-width="120px">
            <el-form-item label="拉人间隔(秒)">
              <el-input-number v-model="newTask.settings.interval" :min="5" :max="300" />
            </el-form-item>
            <el-form-item label="每账号上限">
              <el-input-number v-model="newTask.settings.daily_limit" :min="1" :max="200" />
            </el-form-item>
          </el-form>
          <el-form-item label="任务名称">
            <el-input v-model="newTask.name" placeholder="拉人任务名称" style="width: 100%;" />
          </el-form-item>
        </div>
      </div>

      <template #footer>
        <el-button v-if="wizardStep > 0" @click="wizardStep--">上一步</el-button>
        <el-button v-if="wizardStep < 3" type="primary" @click="wizardStep++">下一步</el-button>
        <el-button v-if="wizardStep === 3" type="primary" @click="submitTask">创建任务</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import TaskCard from '../components/TaskCard.vue'
import { invitesApi } from '../api/index.js'

const tasks = ref([])
const loading = ref(false)
const showCreateWizard = ref(false)
const wizardStep = ref(0)
const sourceType = ref('group')
const sourceGroup = ref('')
const userList = ref('')
const groups = ref([])
const mockAccounts = [{ id: 1, phone: '+1234567890' }, { id: 2, phone: '+0987654321' }]

const newTask = ref({
  name: '',
  account_ids: [],
  target_group: '',
  settings: { interval: 30, daily_limit: 50 },
})

function updateStatus(id, status) {
  const t = tasks.value.find(t => t.id === id)
  if (t) t.status = status
}

async function deleteTask(id) {
  await invitesApi.deleteTask(id)
  tasks.value = tasks.value.filter(t => t.id !== id)
  ElMessage.success('任务已删除')
}

async function submitTask() {
  try {
    const task = await invitesApi.createTask(newTask.value)
    tasks.value.unshift(task)
    showCreateWizard.value = false
    wizardStep.value = 0
    ElMessage.success('拉人任务已创建')
  } catch (err) {
    ElMessage.error('创建失败')
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const [taskList, groupList] = await Promise.all([
      invitesApi.getTasks(),
      invitesApi.getGroups(),
    ])
    tasks.value = taskList
    groups.value = groupList
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.step-content { min-height: 180px; padding: 4px 0; }
.step-desc { color: var(--color-text-muted); font-size: 13px; margin-bottom: 16px; }
.permission-check { margin-top: 8px; display: flex; align-items: center; gap: 6px; font-size: 13px; color: #A6E3A1; }
</style>
