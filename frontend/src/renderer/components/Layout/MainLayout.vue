<template>
  <el-container class="main-layout">
    <el-aside width="200px" class="sidebar-container">
      <Sidebar />
    </el-aside>
    <el-container class="main-content">
      <el-header height="60px" class="topbar-container">
        <TopBar />
      </el-header>
      <el-main class="content-area scrollbar">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import Sidebar from './Sidebar.vue'
import TopBar from './TopBar.vue'
</script>

<style scoped>
.main-layout {
  height: 100vh;
  background-color: var(--color-bg);
}

.sidebar-container {
  background-color: var(--color-sidebar);
  border-right: 1px solid var(--color-border);
  overflow: hidden;
}

.topbar-container {
  background-color: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
  padding: 0;
}

.content-area {
  background-color: var(--color-bg);
  overflow-y: auto;
  padding: 0;
}
</style>
