<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">批量私信</span>
      <el-button type="primary" icon="Plus" @click="showCreateWizard = true">新建任务</el-button>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="全部任务" name="all" />
      <el-tab-pane label="进行中" name="running" />
      <el-tab-pane label="已完成" name="completed" />
    </el-tabs>

    <div v-loading="loading">
      <TaskCard
        v-for="task in filteredTasks"
        :key="task.id"
        :task="task"
        @start="(id) => updateTaskStatus(id, 'running')"
        @pause="(id) => updateTaskStatus(id, 'paused')"
        @stop="(id) => updateTaskStatus(id, 'stopped')"
        @delete="deleteTask"
      />
      <el-empty v-if="filteredTasks.length === 0" description="暂无私信任务" />
    </div>

    <!-- Create Task Wizard -->
    <el-dialog v-model="showCreateWizard" title="新建私信任务" width="680px" destroy-on-close>
      <el-steps :active="wizardStep" finish-status="success" class="wizard-steps">
        <el-step title="选择账号" />
        <el-step title="选择用户" />
        <el-step title="用户筛选" />
        <el-step title="编辑消息" />
        <el-step title="设置参数" />
      </el-steps>

      <div class="wizard-content">
        <div v-if="wizardStep === 0">
          <p class="step-desc">选择发送账号</p>
          <el-checkbox-group v-model="newTask.account_ids">
            <el-checkbox v-for="acc in mockAccounts" :key="acc.id" :label="acc.id">
              {{ acc.phone }}
            </el-checkbox>
          </el-checkbox-group>
        </div>

        <div v-if="wizardStep === 1">
          <p class="step-desc">选择目标用户来源</p>
          <el-radio-group v-model="userSource" class="source-options">
            <el-radio label="manual">手动输入用户名</el-radio>
            <el-radio label="group">从群组提取</el-radio>
            <el-radio label="import">导入列表文件</el-radio>
          </el-radio-group>
          <div v-if="userSource === 'manual'" style="margin-top: 12px;">
            <el-input v-model="manualUsers" type="textarea" :rows="6"
              placeholder="每行一个用户名，如 @username" />
          </div>
          <div v-if="userSource === 'group'" style="margin-top: 12px;">
            <el-select v-model="sourceGroup" placeholder="选择群组" style="width: 100%;">
              <el-option v-for="g in mockGroups" :key="g.id" :label="g.title" :value="String(g.id)" />
            </el-select>
          </div>
        </div>

        <div v-if="wizardStep === 2">
          <p class="step-desc">设置用户筛选条件</p>
          <el-form label-width="140px">
            <el-form-item label="在线状态">
              <el-select v-model="filters.online_status" style="width: 100%;">
                <el-option label="全部用户" value="all" />
                <el-option label="最近在线" value="recently_online" />
                <el-option label="当前在线" value="online" />
              </el-select>
            </el-form-item>
            <el-form-item label="排除已发送">
              <el-switch v-model="filters.exclude_sent" />
            </el-form-item>
            <el-form-item label="排除机器人">
              <el-switch v-model="filters.exclude_bots" />
            </el-form-item>
          </el-form>
        </div>

        <div v-if="wizardStep === 3">
          <p class="step-desc">编辑私信内容（支持个性化变量）</p>
          <el-form>
            <el-form-item label="任务名称">
              <el-input v-model="newTask.name" />
            </el-form-item>
            <el-form-item label="消息模板">
              <el-input v-model="newTask.message_content" type="textarea" :rows="6"
                placeholder="Hello {first_name}, 你好！支持变量: {username} {first_name} {last_name}" />
            </el-form-item>
          </el-form>
          <div class="variable-tips">
            <span>可用变量：</span>
            <el-tag v-for="v in ['username', 'first_name', 'last_name']" :key="v" size="small" class="var-tag">
              {{'{'}}{{ v }}{{'}'}}
            </el-tag>
          </div>
        </div>

        <div v-if="wizardStep === 4">
          <p class="step-desc">配置发送参数</p>
          <el-form label-width="120px">
            <el-form-item label="发送间隔(秒)">
              <el-input-number v-model="newTask.settings.interval" :min="5" :max="300" />
            </el-form-item>
            <el-form-item label="每账号上限">
              <el-input-number v-model="newTask.settings.daily_limit" :min="1" :max="500" />
            </el-form-item>
          </el-form>
        </div>
      </div>

      <template #footer>
        <el-button v-if="wizardStep > 0" @click="wizardStep--">上一步</el-button>
        <el-button v-if="wizardStep < 4" type="primary" @click="wizardStep++">下一步</el-button>
        <el-button v-if="wizardStep === 4" type="primary" @click="submitTask">创建任务</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import TaskCard from '../components/TaskCard.vue'
import { directApi } from '../api/index.js'

const tasks = ref([])
const loading = ref(false)
const activeTab = ref('all')
const showCreateWizard = ref(false)
const wizardStep = ref(0)
const userSource = ref('manual')
const manualUsers = ref('')
const sourceGroup = ref('')
const filters = ref({ online_status: 'all', exclude_sent: true, exclude_bots: true })

const mockAccounts = [{ id: 1, phone: '+1234567890' }, { id: 2, phone: '+0987654321' }]
const mockGroups = [
  { id: -1001234567890, title: '测试群组 A' },
  { id: -1009876543210, title: '测试频道 B' },
]

const newTask = ref({
  name: '',
  account_ids: [],
  message_content: '',
  settings: { interval: 30, daily_limit: 100 },
})

const filteredTasks = computed(() => {
  if (activeTab.value === 'all') return tasks.value
  return tasks.value.filter(t => t.status === activeTab.value)
})

function updateTaskStatus(id, status) {
  const t = tasks.value.find(t => t.id === id)
  if (t) t.status = status
}

async function deleteTask(id) {
  await directApi.deleteTask(id)
  tasks.value = tasks.value.filter(t => t.id !== id)
  ElMessage.success('任务已删除')
}

async function submitTask() {
  try {
    const task = await directApi.createTask(newTask.value)
    tasks.value.unshift(task)
    showCreateWizard.value = false
    wizardStep.value = 0
    ElMessage.success('私信任务已创建')
  } catch (err) {
    ElMessage.error('创建失败')
  }
}

onMounted(async () => {
  loading.value = true
  try {
    tasks.value = await directApi.getTasks()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.wizard-steps { margin-bottom: 24px; }
.wizard-content { min-height: 200px; padding: 8px 0; }
.step-desc { color: var(--color-text-muted); font-size: 13px; margin-bottom: 16px; }
.source-options { display: flex; flex-direction: column; gap: 12px; }
.variable-tips { margin-top: 12px; display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--color-text-muted); }
.var-tag { margin-right: 4px; }
.el-checkbox { display: block; margin-bottom: 8px; }
</style>
