<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">账户检查器</span>
      <div class="header-actions">
        <el-button type="primary" icon="CircleCheck" @click="runCheck" :loading="checking">
          批量检查
        </el-button>
        <el-button icon="Clock" @click="showScheduleDialog = true">定时检查</el-button>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="stats-row" style="margin-bottom: 20px;">
      <StatsCard label="正常账号" :value="summary.normal" icon="CircleCheck" type="success" />
      <StatsCard label="受限账号" :value="summary.restricted" icon="Warning" type="warning" />
      <StatsCard label="封禁账号" :value="summary.banned" icon="CircleClose" type="danger" />
      <StatsCard label="垃圾邮件" :value="summary.spam" icon="MuteNotification" type="danger" />
    </div>

    <el-table v-loading="loading" :data="checkResults" style="width: 100%">
      <el-table-column label="账号" min-width="140">
        <template #default="{ row }">
          <span>账号 #{{ row.account_id }}</span>
        </template>
      </el-table-column>
      <el-table-column label="垃圾邮件" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_spam ? 'danger' : 'success'" size="small">
            {{ row.is_spam ? '是' : '否' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="封禁" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_banned ? 'danger' : 'success'" size="small">
            {{ row.is_banned ? '是' : '否' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="限制" width="80">
        <template #default="{ row }">
          <el-tag :type="row.has_restrictions ? 'warning' : 'success'" size="small">
            {{ row.has_restrictions ? '有' : '无' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="2FA" width="80">
        <template #default="{ row }">
          <el-tag :type="row.two_fa_enabled ? 'primary' : 'info'" size="small">
            {{ row.two_fa_enabled ? '开启' : '关闭' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="健康度" width="120">
        <template #default="{ row }">
          <el-progress
            :percentage="row.health_score"
            :color="scoreColor(row.health_score)"
            :stroke-width="6"
            :show-text="false"
          />
          <span style="font-size: 11px; color: var(--color-text-muted);">{{ row.health_score }}%</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'normal' ? 'success' : 'warning'" size="small">
            {{ row.status === 'normal' ? '正常' : '异常' }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>

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
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import StatsCard from '../components/StatsCard.vue'
import { checkerApi } from '../api/index.js'

const checkResults = ref([])
const loading = ref(false)
const checking = ref(false)
const showScheduleDialog = ref(false)
const scheduleForm = ref({ cron: '0 9 * * *' })

const summary = computed(() => ({
  normal: checkResults.value.filter(r => r.status === 'normal').length,
  restricted: checkResults.value.filter(r => r.has_restrictions).length,
  banned: checkResults.value.filter(r => r.is_banned).length,
  spam: checkResults.value.filter(r => r.is_spam).length,
}))

function scoreColor(score) {
  if (score >= 80) return '#A6E3A1'
  if (score >= 50) return '#FAB387'
  return '#F38BA8'
}

async function runCheck() {
  checking.value = true
  try {
    const result = await checkerApi.check({ account_ids: [1, 2, 3] })
    checkResults.value = result.results
    ElMessage.success(`检查完成，共 ${result.checked} 个账号`)
  } catch (err) {
    ElMessage.error('检查失败')
  } finally {
    checking.value = false
  }
}

async function saveSchedule() {
  try {
    await checkerApi.schedule({ account_ids: [1, 2, 3], cron: scheduleForm.value.cron })
    ElMessage.success('定时检查已设置')
    showScheduleDialog.value = false
  } catch (err) {
    ElMessage.error('设置失败')
  }
}

onMounted(runCheck)
</script>
