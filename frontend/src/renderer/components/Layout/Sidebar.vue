<template>
  <div class="sidebar">
    <div class="sidebar-logo">
      <el-icon size="24" color="#409EFF"><Grid /></el-icon>
      <span class="logo-text">PushMatrix</span>
    </div>

    <el-menu
      :default-active="activeMenu"
      router
      class="sidebar-menu"
    >
      <el-sub-menu index="accounts">
        <template #title>
          <el-icon><User /></el-icon>
          <span>账号管理</span>
        </template>
        <el-menu-item index="/accounts/list">账号列表</el-menu-item>
        <el-menu-item index="/accounts/import">批量导入</el-menu-item>
      </el-sub-menu>

      <el-menu-item index="/proxies">
        <el-icon><Connection /></el-icon>
        <span>代理管理</span>
      </el-menu-item>

      <el-menu-item index="/bulk-message">
        <el-icon><ChatDotSquare /></el-icon>
        <span>群发消息</span>
      </el-menu-item>

      <el-menu-item index="/direct-message">
        <el-icon><ChatLineSquare /></el-icon>
        <span>批量私信</span>
      </el-menu-item>

      <el-menu-item index="/invite">
        <el-icon><UserFilled /></el-icon>
        <span>批量拉人</span>
      </el-menu-item>

      <el-menu-item index="/checker">
        <el-icon><CircleCheck /></el-icon>
        <span>账户检查</span>
      </el-menu-item>

      <el-menu-item index="/profile">
        <el-icon><Edit /></el-icon>
        <span>资料管理</span>
      </el-menu-item>

      <el-menu-item index="/stats">
        <el-icon><TrendCharts /></el-icon>
        <span>数据统计</span>
      </el-menu-item>

      <el-menu-item index="/settings">
        <el-icon><Setting /></el-icon>
        <span>系统设置</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--color-sidebar);
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
  height: 60px;
}

.logo-text {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: 0.5px;
}

.sidebar-menu {
  flex: 1;
  overflow-y: auto;
  padding-top: 8px;
}

.sidebar-menu::-webkit-scrollbar {
  width: 4px;
}

.sidebar-menu::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 2px;
}
</style>
