<template>
  <div class="stat-card" :style="{ borderLeftColor: color }">
    <div class="stat-card__value">{{ value }}</div>
    <div class="stat-card__label">{{ label }}</div>
  </div>
</template>

<script setup>
defineProps({
  value: { type: [String, Number], required: true },
  label: { type: String, required: true },
  color: { type: String, default: '#10b981' },
})
</script>

<style scoped>
.stat-card {
  background: #252938;
  border-left: 4px solid;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-card__value {
  font-size: 32px;
  font-weight: bold;
  color: #e5e7eb;
}

.stat-card__label {
  font-size: 14px;
  color: #9ca3af;
}
</style>
