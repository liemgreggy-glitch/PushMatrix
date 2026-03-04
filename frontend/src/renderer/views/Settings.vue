<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">系统设置</span>
      <el-button type="primary" icon="Check" @click="saveSettings" :loading="saving">保存设置</el-button>
    </div>

    <el-tabs v-model="activeTab">
      <!-- Telegram API Settings -->
      <el-tab-pane label="Telegram API" name="telegram">
        <el-card class="settings-card">
          <el-form :model="settings.telegram" label-width="140px">
            <el-form-item label="API ID">
              <el-input v-model="settings.telegram.api_id" placeholder="从 my.telegram.org 获取" style="max-width: 300px;" />
            </el-form-item>
            <el-form-item label="API Hash">
              <el-input v-model="settings.telegram.api_hash" type="password" placeholder="API Hash" show-password style="max-width: 400px;" />
            </el-form-item>
            <el-form-item>
              <el-button @click="testConnection" :loading="testing">测试连接</el-button>
              <span v-if="connectionStatus" class="connection-status" :class="connectionStatus">
                {{ connectionStatus === 'success' ? '✅ 连接成功' : '❌ 连接失败' }}
              </span>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- Rate Control Settings -->
      <el-tab-pane label="风控设置" name="rate">
        <el-card class="settings-card">
          <el-form :model="settings.rate_control" label-width="160px">
            <el-form-item label="全局发送间隔(秒)">
              <el-input-number v-model="settings.rate_control.global_interval" :min="5" :max="300" />
              <span class="form-hint">每条消息之间的最小间隔时间</span>
            </el-form-item>
            <el-form-item label="每日发送上限">
              <el-input-number v-model="settings.rate_control.daily_limit" :min="1" :max="1000" />
              <span class="form-hint">每个账号每天最多发送数量</span>
            </el-form-item>
            <el-form-item label="最大随机延迟(秒)">
              <el-input-number v-model="settings.rate_control.max_random_delay" :min="0" :max="60" />
              <span class="form-hint">在固定间隔基础上增加随机延迟</span>
            </el-form-item>
            <el-form-item label="异常错误阈值">
              <el-input-number v-model="settings.rate_control.error_threshold" :min="1" :max="100" />
              <span class="form-hint">连续失败超过此次数则暂停账号</span>
            </el-form-item>
            <el-form-item label="冷启动延迟(秒)">
              <el-input-number v-model="settings.rate_control.cold_start_delay" :min="0" :max="3600" />
              <span class="form-hint">新账号首次发送前的预热时间</span>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- Database Settings -->
      <el-tab-pane label="数据库设置" name="database">
        <el-card class="settings-card">
          <el-form :model="settings.database" label-width="140px">
            <el-form-item label="数据库连接">
              <el-input v-model="settings.database.url" placeholder="sqlite:///./pushmatrix.db" style="max-width: 500px;" />
            </el-form-item>
            <el-form-item label="自动备份">
              <el-switch v-model="settings.database.backup_enabled" />
            </el-form-item>
            <el-form-item v-if="settings.database.backup_enabled" label="备份间隔(天)">
              <el-input-number v-model="settings.database.backup_interval_days" :min="1" :max="30" />
            </el-form-item>
          </el-form>
          <div class="db-actions">
            <el-button icon="Download" @click="backup">立即备份</el-button>
            <el-button icon="Upload" @click="showRestoreDialog = true">还原数据库</el-button>
            <el-button icon="Delete" type="warning" @click="clearLogs">清理旧日志</el-button>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- Notification Settings -->
      <el-tab-pane label="通知设置" name="notifications">
        <el-card class="settings-card">
          <el-form :model="settings.notifications" label-width="160px">
            <el-form-item label="任务完成通知">
              <el-switch v-model="settings.notifications.on_task_complete" />
            </el-form-item>
            <el-form-item label="异常告警通知">
              <el-switch v-model="settings.notifications.on_error" />
            </el-form-item>
            <el-form-item label="通知方式">
              <el-select v-model="settings.notifications.method" style="width: 200px;">
                <el-option label="不通知" value="none" />
                <el-option label="邮件通知" value="email" />
                <el-option label="Telegram 通知" value="telegram" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="settings.notifications.method !== 'none'" label="通知目标">
              <el-input
                v-model="settings.notifications.target"
                :placeholder="settings.notifications.method === 'email' ? '邮箱地址' : 'Telegram 用户名或 Chat ID'"
                style="max-width: 300px;"
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- Restore Dialog -->
    <el-dialog v-model="showRestoreDialog" title="还原数据库" width="400px">
      <el-input v-model="restoreFile" placeholder="备份文件名，如 pushmatrix_backup_20240101.db" />
      <template #footer>
        <el-button @click="showRestoreDialog = false">取消</el-button>
        <el-button type="warning" @click="restore">还原</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { settingsApi } from '../api/index.js'

const activeTab = ref('telegram')
const saving = ref(false)
const testing = ref(false)
const connectionStatus = ref('')
const showRestoreDialog = ref(false)
const restoreFile = ref('')

const settings = ref({
  telegram: { api_id: null, api_hash: '' },
  rate_control: { global_interval: 30, daily_limit: 100, max_random_delay: 10, error_threshold: 5, cold_start_delay: 60 },
  database: { url: 'sqlite:///./pushmatrix.db', backup_enabled: true, backup_interval_days: 7 },
  notifications: { on_task_complete: true, on_error: true, method: 'none', target: '' },
})

async function loadSettings() {
  try {
    const data = await settingsApi.get()
    settings.value = { ...settings.value, ...data }
  } catch (err) {
    console.error('Failed to load settings')
  }
}

async function saveSettings() {
  saving.value = true
  try {
    await settingsApi.update(settings.value)
    ElMessage.success('设置已保存')
  } catch (err) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function testConnection() {
  testing.value = true
  connectionStatus.value = ''
  try {
    await settingsApi.testConnection({
      api_id: settings.value.telegram.api_id,
      api_hash: settings.value.telegram.api_hash,
      phone: '+1234567890',
    })
    connectionStatus.value = 'success'
  } catch (err) {
    connectionStatus.value = 'error'
  } finally {
    testing.value = false
  }
}

async function backup() {
  try {
    const result = await settingsApi.backup()
    ElMessage.success(`备份成功: ${result.backup_file}`)
  } catch (err) {
    ElMessage.error('备份失败')
  }
}

async function restore() {
  if (!restoreFile.value) return
  await ElMessageBox.confirm('还原数据库将覆盖当前数据，确定继续吗？', '警告', { type: 'warning' })
  try {
    await settingsApi.restore(restoreFile.value)
    ElMessage.success('数据库已还原')
    showRestoreDialog.value = false
  } catch (err) {
    ElMessage.error('还原失败')
  }
}

async function clearLogs() {
  await ElMessageBox.confirm('确定清理 30 天前的日志吗？', '确认', { type: 'warning' })
  try {
    const result = await settingsApi.clearLogs(30)
    ElMessage.success(`已清理 ${result.deleted_records} 条日志`)
  } catch (err) {
    ElMessage.error('清理失败')
  }
}

onMounted(loadSettings)
</script>

<style scoped>
.settings-card { max-width: 700px; }
.form-hint { margin-left: 12px; font-size: 12px; color: var(--color-text-muted); }
.connection-status { margin-left: 12px; font-size: 13px; }
.connection-status.success { color: var(--color-success); }
.connection-status.error { color: var(--color-danger); }
.db-actions { display: flex; gap: 12px; margin-top: 16px; }
</style>
