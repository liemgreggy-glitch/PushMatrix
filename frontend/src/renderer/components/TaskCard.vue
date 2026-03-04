<template>
  <el-card class="task-card">
    <div class="task-header">
      <div class="task-info">
        <span class="task-name">{{ task.name }}</span>
        <el-tag :type="statusType(task.status)" size="small">
          {{ statusLabel(task.status) }}
        </el-tag>
      </div>
      <div class="task-actions">
        <el-button
          v-if="task.status === 'pending' || task.status === 'paused'"
          circle
          icon="VideoPlay"
          size="small"
          type="success"
          @click="emit('start', task.id)"
        />
        <el-button
          v-if="task.status === 'running'"
          circle
          icon="VideoPause"
          size="small"
          type="warning"
          @click="emit('pause', task.id)"
        />
        <el-button
          v-if="task.status === 'running' || task.status === 'paused'"
          circle
          icon="VideoPlay"
          size="small"
          type="danger"
          @click="emit('stop', task.id)"
        />
        <el-button
          circle
          icon="Delete"
          size="small"
          @click="emit('delete', task.id)"
        />
      </div>
    </div>

    <div class="task-progress">
      <el-progress
        :percentage="progressPercent"
        :status="progressStatus"
        :stroke-width="8"
      />
      <div class="progress-stats">
        <span>{{ task.success_count }} 成功</span>
        <span class="text-danger">{{ task.failed_count }} 失败</span>
        <span class="text-muted">{{ task.progress }} / {{ task.total }}</span>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  task: { type: Object, required: true },
})

const emit = defineEmits(['start', 'pause', 'stop', 'delete'])

const progressPercent = computed(() =>
  props.task.total > 0 ? Math.round((props.task.progress / props.task.total) * 100) : 0
)

const progressStatus = computed(() => {
  if (props.task.status === 'completed') return 'success'
  if (props.task.status === 'failed') return 'exception'
  return ''
})

function statusType(status) {
  const map = { pending: 'info', running: 'primary', paused: 'warning', completed: 'success', failed: 'danger' }
  return map[status] || 'info'
}

function statusLabel(status) {
  const map = { pending: '待执行', running: '进行中', paused: '已暂停', completed: '已完成', failed: '失败' }
  return map[status] || status
}
</script>

<style scoped>
.task-card {
  margin-bottom: 12px;
}

.task-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.task-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.task-name {
  font-weight: 600;
  color: var(--color-text);
}

.task-actions {
  display: flex;
  gap: 6px;
}

.task-progress {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.progress-stats {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--color-text-muted);
}
</style>
