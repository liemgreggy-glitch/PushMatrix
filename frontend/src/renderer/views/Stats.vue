<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">数据统计</span>
      <div class="header-actions">
        <el-select v-model="period" style="width: 120px;" @change="loadData">
          <el-option label="最近7天" :value="7" />
          <el-option label="最近30天" :value="30" />
          <el-option label="最近90天" :value="90" />
        </el-select>
        <el-button icon="Download" @click="exportReport">导出报表</el-button>
      </div>
    </div>

    <!-- Overview Cards -->
    <div class="stats-row">
      <StatsCard label="总发送量" :value="taskStats.total_sent" icon="ChatDotSquare" type="info" />
      <StatsCard label="成功率" :value="`${taskStats.completion_rate}%`" icon="TrendCharts" type="success" />
      <StatsCard label="完成任务" :value="taskStats.completed" icon="CircleCheck" type="success" />
      <StatsCard label="失败任务" :value="taskStats.failed" icon="CircleClose" type="danger" />
    </div>

    <el-row :gutter="16">
      <!-- Send Volume Chart -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>发送量趋势（{{ period }}天）</span>
            </div>
          </template>
          <div class="chart-container">
            <div class="bar-chart">
              <div
                v-for="(val, i) in chartData.datasets[0]?.data || []"
                :key="i"
                class="bar-item"
              >
                <div class="bar-fill" :style="{ height: `${(val / maxVal) * 100}%` }">
                  <span class="bar-val">{{ val }}</span>
                </div>
                <span class="bar-label">{{ chartData.labels[i] }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Task Type Distribution -->
      <el-col :span="8">
        <el-card>
          <template #header><span>任务类型分布</span></template>
          <div class="type-dist">
            <div v-for="(count, type) in taskStats.by_type" :key="type" class="type-item">
              <div class="type-info">
                <span class="type-dot" :class="`type-dot--${type}`" />
                <span>{{ typeLabel(type) }}</span>
              </div>
              <div class="type-bar-wrap">
                <el-progress
                  :percentage="Math.round((count / taskStats.total_tasks) * 100)"
                  :color="typeColor(type)"
                  :stroke-width="8"
                  :show-text="false"
                />
                <span class="type-count">{{ count }}</span>
              </div>
            </div>
          </div>
        </el-card>

        <el-card style="margin-top: 16px;">
          <template #header><span>账号状态统计</span></template>
          <div class="account-dist">
            <div v-for="(count, status) in accountStats.by_status" :key="status" class="acc-stat-item">
              <span class="acc-stat-label">{{ statusLabel(status) }}</span>
              <el-progress :percentage="Math.round((count / accountStats.total) * 100)" :stroke-width="6" :show-text="false" />
              <span class="acc-stat-count">{{ count }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Detailed Table -->
    <el-card style="margin-top: 16px;">
      <template #header><span>发送记录统计</span></template>
      <el-table :data="tableData" style="width: 100%">
        <el-table-column label="日期" prop="date" width="120" />
        <el-table-column label="发送成功" prop="success" min-width="100">
          <template #default="{ row }">
            <span class="text-success">{{ row.success }}</span>
          </template>
        </el-table-column>
        <el-table-column label="发送失败" prop="failed" min-width="100">
          <template #default="{ row }">
            <span class="text-danger">{{ row.failed }}</span>
          </template>
        </el-table-column>
        <el-table-column label="成功率" min-width="120">
          <template #default="{ row }">
            <el-progress :percentage="row.rate" :stroke-width="6" :show-text="false" />
            <span style="font-size: 12px; margin-left: 6px;">{{ row.rate }}%</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import StatsCard from '../components/StatsCard.vue'
import { statsApi } from '../api/index.js'

const period = ref(7)
const chartData = ref({ labels: [], datasets: [] })
const taskStats = ref({ total_sent: 0, completion_rate: 0, completed: 0, failed: 0, total_tasks: 1, by_type: {} })
const accountStats = ref({ total: 1, by_status: {} })

const maxVal = computed(() => Math.max(...(chartData.value.datasets[0]?.data || [1])))

const tableData = computed(() => {
  const labels = chartData.value.labels || []
  const success = chartData.value.datasets[0]?.data || []
  const failed = chartData.value.datasets[1]?.data || []
  return labels.map((label, i) => ({
    date: label,
    success: success[i] || 0,
    failed: failed[i] || 0,
    rate: success[i] ? Math.round((success[i] / (success[i] + (failed[i] || 0))) * 100) : 0,
  }))
})

function typeLabel(t) {
  return { bulk_message: '群发消息', direct_message: '批量私信', invite: '批量拉人' }[t] || t
}

function typeColor(t) {
  return { bulk_message: '#409EFF', direct_message: '#A6E3A1', invite: '#FAB387' }[t] || '#6C7086'
}

function statusLabel(s) {
  return { online: '在线', offline: '离线', frozen: '冻结', spam: '受限' }[s] || s
}

async function loadData() {
  const [chart, tasks, accounts] = await Promise.all([
    statsApi.getChartData(period.value).catch(() => chartData.value),
    statsApi.getTaskStats(period.value).catch(() => taskStats.value),
    statsApi.getAccountStats().catch(() => accountStats.value),
  ])
  chartData.value = chart
  taskStats.value = tasks
  accountStats.value = accounts
}

async function exportReport() {
  const result = await statsApi.export({ format: 'excel', days: period.value }).catch(() => null)
  if (result) ElMessage.success('报表已生成，正在下载...')
}

onMounted(loadData)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.chart-container { height: 200px; }
.bar-chart { display: flex; align-items: flex-end; gap: 8px; height: 100%; padding-bottom: 24px; }
.bar-item { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; }
.bar-fill {
  width: 100%;
  background: linear-gradient(to top, #409EFF, #89b4fa);
  border-radius: 2px 2px 0 0;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  min-height: 4px;
  transition: height 0.3s;
  position: relative;
  flex-shrink: 0;
}
.bar-val { font-size: 10px; color: white; margin-top: 2px; }
.bar-label { font-size: 10px; color: var(--color-text-muted); margin-top: 4px; }

.type-dist, .account-dist { display: flex; flex-direction: column; gap: 14px; }
.type-item { display: flex; flex-direction: column; gap: 4px; }
.type-info { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.type-dot { width: 10px; height: 10px; border-radius: 50%; }
.type-dot--bulk_message { background: #409EFF; }
.type-dot--direct_message { background: #A6E3A1; }
.type-dot--invite { background: #FAB387; }
.type-bar-wrap { display: flex; align-items: center; gap: 8px; }
.type-count { font-size: 12px; color: var(--color-text-muted); min-width: 24px; }

.acc-stat-item { display: flex; align-items: center; gap: 10px; }
.acc-stat-label { width: 40px; font-size: 13px; flex-shrink: 0; }
.acc-stat-count { width: 30px; font-size: 12px; text-align: right; flex-shrink: 0; }
</style>
