<template>
  <div class="page-container">
    <!-- Stats Cards -->
    <div class="stats-row">
      <StatsCard label="账号总数" :value="overview.total_accounts" icon="User" type="default" />
      <StatsCard label="在线账号" :value="overview.online_accounts" icon="Connection" type="success" />
      <StatsCard label="今日发送" :value="overview.today_sent" icon="ChatDotSquare" type="info" />
      <StatsCard label="成功率" :value="`${overview.success_rate}%`" icon="TrendCharts" type="warning" />
    </div>

    <el-row :gutter="16">
      <!-- Chart -->
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>发送量趋势</span>
              <el-radio-group v-model="chartDays" size="small" @change="loadChartData">
                <el-radio-button :label="7">7天</el-radio-button>
                <el-radio-button :label="30">30天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div class="chart-placeholder">
            <div class="chart-bars">
              <div
                v-for="(val, i) in chartData.datasets[0]?.data || []"
                :key="i"
                class="chart-bar"
                :style="{ height: `${(val / maxChartVal) * 100}%` }"
              />
            </div>
            <div class="chart-labels">
              <span v-for="label in chartData.labels" :key="label" class="chart-label">{{ label }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Recent Tasks -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近任务</span>
              <el-button text size="small" @click="$router.push('/bulk-message')">查看全部</el-button>
            </div>
          </template>
          <div v-if="recentTasks.length === 0" class="empty-state">
            <el-empty description="暂无任务" :image-size="60" />
          </div>
          <div v-else>
            <div v-for="task in recentTasks" :key="task.id" class="task-item">
              <div class="task-item-info">
                <span class="task-item-name">{{ task.name }}</span>
                <el-tag :type="taskStatusType(task.status)" size="small">
                  {{ taskStatusLabel(task.status) }}
                </el-tag>
              </div>
              <el-progress
                :percentage="taskProgress(task)"
                :stroke-width="4"
                :show-text="false"
              />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Account Status Distribution -->
    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="12">
        <el-card>
          <template #header><span>账号状态分布</span></template>
          <div class="status-dist">
            <div v-for="(count, status) in accountStats.by_status" :key="status" class="status-item">
              <span class="status-dot" :class="`status-dot--${status}`" />
              <span class="status-name">{{ statusLabel(status) }}</span>
              <span class="status-count">{{ count }}</span>
              <el-progress
                :percentage="Math.round((count / accountStats.total) * 100)"
                :color="statusColor(status)"
                :stroke-width="6"
                :show-text="false"
                style="flex: 1;"
              />
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>系统状态</span></template>
          <div class="system-stats">
            <div class="sys-item">
              <span class="sys-label">活跃任务</span>
              <span class="sys-value">{{ overview.active_tasks }}</span>
            </div>
            <div class="sys-item">
              <span class="sys-label">已完成任务</span>
              <span class="sys-value">{{ overview.total_tasks_completed }}</span>
            </div>
            <div class="sys-item">
              <span class="sys-label">API 调用今日</span>
              <span class="sys-value">{{ performance.api_calls_today }}</span>
            </div>
            <div class="sys-item">
              <span class="sys-label">平均响应时间</span>
              <span class="sys-value">{{ performance.avg_response_time_ms }}ms</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import StatsCard from '../components/StatsCard.vue'
import { statsApi, tasksApi } from '../api/index.js'

const overview = ref({ total_accounts: 0, online_accounts: 0, today_sent: 0, success_rate: 0, active_tasks: 0, total_tasks_completed: 0 })
const chartData = ref({ labels: [], datasets: [] })
const chartDays = ref(7)
const recentTasks = ref([])
const accountStats = ref({ total: 1, by_status: {} })
const performance = ref({ api_calls_today: 0, avg_response_time_ms: 0 })

const maxChartVal = computed(() => {
  const data = chartData.value.datasets[0]?.data || []
  return Math.max(...data, 1)
})

async function loadData() {
  const [ov, chart, tasks, aStats, perf] = await Promise.all([
    statsApi.getOverview().catch(() => overview.value),
    statsApi.getChartData(chartDays.value).catch(() => chartData.value),
    tasksApi.getRecent(5).catch(() => []),
    statsApi.getAccountStats().catch(() => accountStats.value),
    statsApi.getPerformance().catch(() => performance.value),
  ])
  overview.value = ov
  chartData.value = chart
  recentTasks.value = tasks
  accountStats.value = aStats
  performance.value = perf
}

async function loadChartData() {
  chartData.value = await statsApi.getChartData(chartDays.value).catch(() => chartData.value)
}

function taskProgress(task) {
  return task.total > 0 ? Math.round((task.progress / task.total) * 100) : 0
}

function taskStatusType(s) {
  return { running: 'primary', completed: 'success', failed: 'danger', paused: 'warning', pending: 'info' }[s] || 'info'
}

function taskStatusLabel(s) {
  return { running: '进行中', completed: '完成', failed: '失败', paused: '暂停', pending: '待执行' }[s] || s
}

function statusLabel(s) {
  return { online: '在线', offline: '离线', frozen: '冻结', spam: '受限' }[s] || s
}

function statusColor(s) {
  return { online: '#A6E3A1', offline: '#6C7086', frozen: '#FAB387', spam: '#F38BA8' }[s] || '#6C7086'
}

onMounted(loadData)
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chart-placeholder {
  height: 200px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chart-bars {
  flex: 1;
  display: flex;
  align-items: flex-end;
  gap: 6px;
  padding: 0 4px;
}

.chart-bar {
  flex: 1;
  background: linear-gradient(to top, #409EFF, #89b4fa);
  border-radius: 2px 2px 0 0;
  min-height: 4px;
  transition: height 0.3s ease;
}

.chart-labels {
  display: flex;
  gap: 6px;
  padding: 0 4px;
}

.chart-label {
  flex: 1;
  font-size: 11px;
  color: var(--color-text-muted);
  text-align: center;
}

.task-item {
  padding: 8px 0;
  border-bottom: 1px solid var(--color-border);
}

.task-item:last-child {
  border-bottom: none;
}

.task-item-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.task-item-name {
  font-size: 13px;
  color: var(--color-text);
}

.status-dist {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot--online { background-color: #A6E3A1; }
.status-dot--offline { background-color: #6C7086; }
.status-dot--frozen { background-color: #FAB387; }
.status-dot--spam { background-color: #F38BA8; }

.status-name {
  width: 40px;
  font-size: 13px;
  color: var(--color-text);
}

.status-count {
  width: 30px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
}

.system-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.sys-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sys-label {
  font-size: 12px;
  color: var(--color-text-muted);
}

.sys-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text);
}
</style>
