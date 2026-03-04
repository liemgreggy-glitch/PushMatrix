<template>
  <el-card class="stats-card" :class="`stats-card--${type}`">
    <div class="stats-card-content">
      <div class="stats-info">
        <span class="stats-label">{{ label }}</span>
        <span class="stats-value">{{ value }}</span>
        <span v-if="subLabel" class="stats-sub">{{ subLabel }}</span>
      </div>
      <div class="stats-icon">
        <el-icon :size="32"><component :is="icon" /></el-icon>
      </div>
    </div>
    <div v-if="trend !== undefined" class="stats-trend">
      <el-icon :class="trend >= 0 ? 'trend-up' : 'trend-down'">
        <component :is="trend >= 0 ? 'ArrowUp' : 'ArrowDown'" />
      </el-icon>
      <span :class="trend >= 0 ? 'trend-up' : 'trend-down'">
        {{ Math.abs(trend) }}% 较昨日
      </span>
    </div>
  </el-card>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  subLabel: { type: String, default: '' },
  icon: { type: String, default: 'DataBoard' },
  type: { type: String, default: 'default' }, // default/success/warning/danger/info
  trend: { type: Number, default: undefined },
})
</script>

<style scoped>
.stats-card {
  background-color: var(--color-bg-card);
  border-color: var(--color-border);
  cursor: default;
}

.stats-card--success { border-left: 3px solid var(--color-success); }
.stats-card--warning { border-left: 3px solid var(--color-warning); }
.stats-card--danger  { border-left: 3px solid var(--color-danger); }
.stats-card--info    { border-left: 3px solid var(--color-info); }
.stats-card--default { border-left: 3px solid var(--color-primary); }

.stats-card-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stats-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stats-label {
  font-size: 13px;
  color: var(--color-text-muted);
}

.stats-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
}

.stats-sub {
  font-size: 12px;
  color: var(--color-text-muted);
}

.stats-icon {
  color: var(--color-text-muted);
  opacity: 0.5;
}

.stats-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  font-size: 12px;
}

.trend-up { color: var(--color-success); }
.trend-down { color: var(--color-danger); }
</style>
