<template>
  <div class="topbar">
    <div class="topbar-left">
      <span class="current-page">{{ pageTitle }}</span>
    </div>
    <div class="topbar-right">
      <el-tooltip content="刷新" placement="bottom">
        <el-button
          circle
          icon="Refresh"
          size="small"
          class="topbar-btn"
          @click="refresh"
        />
      </el-tooltip>
      <el-tooltip content="全屏" placement="bottom">
        <el-button
          circle
          icon="FullScreen"
          size="small"
          class="topbar-btn"
          @click="toggleFullscreen"
        />
      </el-tooltip>
      <div class="divider" />
      <div class="status-indicator">
        <span class="status-dot online" />
        <span class="status-text">后端连接正常</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const pageTitle = computed(() => route.meta?.title || 'PushMatrix')

function refresh() {
  window.location.reload()
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}
</script>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 20px;
  background-color: var(--color-bg);
}

.current-page {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.topbar-btn {
  background: transparent;
  border-color: var(--color-border);
  color: var(--color-text-muted);
}

.divider {
  width: 1px;
  height: 20px;
  background-color: var(--color-border);
  margin: 0 8px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--color-text-muted);
}

.status-dot.online {
  background-color: var(--color-success);
}

.status-text {
  font-size: 12px;
  color: var(--color-text-muted);
}
</style>
