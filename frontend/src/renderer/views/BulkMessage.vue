<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">群发消息</span>
      <el-button type="primary" icon="Plus" @click="showCreateWizard = true">新建任务</el-button>
    </div>

    <!-- Task List -->
    <el-tabs v-model="activeTab">
      <el-tab-pane label="全部任务" name="all" />
      <el-tab-pane label="进行中" name="running" />
      <el-tab-pane label="已完成" name="completed" />
      <el-tab-pane label="失败" name="failed" />
    </el-tabs>

    <div v-loading="loading">
      <TaskCard
        v-for="task in filteredTasks"
        :key="task.id"
        :task="task"
        @start="startTask"
        @pause="pauseTask"
        @stop="stopTask"
        @delete="deleteTask"
      />
      <el-empty v-if="filteredTasks.length === 0" description="暂无任务" />
    </div>

    <!-- Create Task Dialog/Wizard -->
    <el-dialog v-model="showCreateWizard" title="新建群发任务" width="680px" destroy-on-close>
      <el-steps :active="wizardStep" finish-status="success" class="wizard-steps">
        <el-step title="选择账号" />
        <el-step title="选择群组" />
        <el-step title="编辑消息" />
        <el-step title="设置参数" />
      </el-steps>

      <div class="wizard-content">
        <!-- Step 1: Select Accounts -->
        <div v-if="wizardStep === 0">
          <p class="step-desc">选择用于发送的 Telegram 账号</p>
          <el-checkbox-group v-model="newTask.account_ids">
            <el-checkbox v-for="acc in mockAccounts" :key="acc.id" :label="acc.id">
              {{ acc.phone }} ({{ acc.status }})
            </el-checkbox>
          </el-checkbox-group>
        </div>

        <!-- Step 2: Select Groups -->
        <div v-if="wizardStep === 1">
          <p class="step-desc">选择目标群组或频道</p>
          <el-input v-model="groupSearch" placeholder="搜索群组..." prefix-icon="Search" style="margin-bottom: 12px;" />
          <el-checkbox-group v-model="newTask.target_groups">
            <el-checkbox v-for="g in mockGroups" :key="g.id" :label="String(g.id)">
              {{ g.title }} ({{ g.members }} 成员)
            </el-checkbox>
          </el-checkbox-group>
        </div>

        <!-- Step 3: Message Content -->
        <div v-if="wizardStep === 2">
          <p class="step-desc">编辑发送内容</p>
          <el-form>
            <el-form-item label="任务名称">
              <el-input v-model="newTask.name" placeholder="群发任务名称" />
            </el-form-item>
            <el-form-item label="消息内容">
              <el-input
                v-model="newTask.message_content"
                type="textarea"
                :rows="6"
                placeholder="输入消息内容..."
              />
            </el-form-item>
            <el-form-item label="消息模板">
              <el-select v-model="selectedTemplate" placeholder="选择模板（可选）" clearable style="width: 100%;">
                <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <!-- Step 4: Settings -->
        <div v-if="wizardStep === 3">
          <p class="step-desc">配置发送参数</p>
          <el-form label-width="120px">
            <el-form-item label="发送间隔(秒)">
              <el-input-number v-model="newTask.settings.interval" :min="5" :max="300" />
            </el-form-item>
            <el-form-item label="每账号上限">
              <el-input-number v-model="newTask.settings.daily_limit" :min="1" :max="500" />
            </el-form-item>
            <el-form-item label="随机延迟(秒)">
              <el-input-number v-model="newTask.settings.max_random_delay" :min="0" :max="60" />
            </el-form-item>
            <el-form-item label="定时发送">
              <el-date-picker
                v-model="newTask.settings.scheduled_at"
                type="datetime"
                placeholder="立即执行（可选）"
                style="width: 100%;"
              />
            </el-form-item>
          </el-form>
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import TaskCard from '../components/TaskCard.vue'
import { messagesApi } from '../api/index.js'

const tasks = ref([])
const loading = ref(false)
const activeTab = ref('all')
const showCreateWizard = ref(false)
const wizardStep = ref(0)
const groupSearch = ref('')
const selectedTemplate = ref(null)
const templates = ref([])

const mockAccounts = [
  { id: 1, phone: '+1234567890', status: 'online' },
  { id: 2, phone: '+0987654321', status: 'offline' },
]
const mockGroups = [
  { id: -1001234567890, title: '测试群组 A', members: 1500 },
  { id: -1009876543210, title: '测试频道 B', members: 5000 },
]

const newTask = ref({
  name: '',
  account_ids: [],
  target_groups: [],
  message_content: '',
  settings: { interval: 30, daily_limit: 100, max_random_delay: 10, scheduled_at: null },
})

const filteredTasks = computed(() => {
  if (activeTab.value === 'all') return tasks.value
  return tasks.value.filter(t => t.status === activeTab.value)
})

async function startTask(id) {
  await messagesApi.startTask(id)
  const t = tasks.value.find(t => t.id === id)
  if (t) t.status = 'running'
}

async function pauseTask(id) {
  await messagesApi.pauseTask(id)
  const t = tasks.value.find(t => t.id === id)
  if (t) t.status = 'paused'
}

async function stopTask(id) {
  await messagesApi.stopTask(id)
  const t = tasks.value.find(t => t.id === id)
  if (t) t.status = 'stopped'
}

async function deleteTask(id) {
  await messagesApi.deleteTask(id)
  tasks.value = tasks.value.filter(t => t.id !== id)
  ElMessage.success('任务已删除')
}

async function submitTask() {
  try {
    const task = await messagesApi.createTask(newTask.value)
    tasks.value.unshift(task)
    showCreateWizard.value = false
    wizardStep.value = 0
    ElMessage.success('任务已创建')
  } catch (err) {
    ElMessage.error('创建失败')
  }
}

onMounted(async () => {
  loading.value = true
  try {
    tasks.value = await messagesApi.getTasks()
    templates.value = await messagesApi.getTemplates()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.wizard-steps {
  margin-bottom: 24px;
}

.wizard-content {
  min-height: 200px;
  padding: 8px 0;
}

.step-desc {
  color: var(--color-text-muted);
  font-size: 13px;
  margin-bottom: 16px;
}

.el-checkbox {
  display: block;
  margin-bottom: 8px;
}
</style>
