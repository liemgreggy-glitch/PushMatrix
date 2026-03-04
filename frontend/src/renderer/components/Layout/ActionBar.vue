<template>
  <transition name="slide-down">
    <div v-if="selectedCount > 0" class="action-bar">
      <div class="selected-info">
        <el-button
          circle
          icon="Close"
          size="small"
          @click="emit('clear-selection')"
        />
        <span>已选中账户: {{ selectedCount }} / {{ total }}</span>
      </div>

      <div class="action-buttons">
        <el-tooltip content="统计" placement="bottom">
          <el-button circle icon="TrendCharts" size="small" @click="emit('action', 'stats')" />
        </el-tooltip>
        <el-tooltip content="标签" placement="bottom">
          <el-button circle icon="PriceTag" size="small" @click="emit('action', 'tag')" />
        </el-tooltip>
        <el-tooltip content="复制" placement="bottom">
          <el-button circle icon="DocumentCopy" size="small" @click="emit('action', 'copy')" />
        </el-tooltip>

        <el-dropdown trigger="click" @command="(cmd) => emit('action', cmd)">
          <el-button type="primary" size="small">
            行动
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="activate">✅ 激活选中账户</el-dropdown-item>
              <el-dropdown-item command="check">⚠️ 批量检查账户状态</el-dropdown-item>
              <el-dropdown-item command="open-web">🌐 在 Telegram Web 打开</el-dropdown-item>
              <el-dropdown-item command="2fa">🔑 批量配置 2FA</el-dropdown-item>
              <el-dropdown-item command="tag">🏷️ 批量修改标签/分组</el-dropdown-item>
              <el-dropdown-item command="get-profile">💬 批量获取个人资料</el-dropdown-item>
              <el-dropdown-item command="edit-profile">📝 批量修改昵称/头像</el-dropdown-item>
              <el-dropdown-item command="privacy">⚙️ 批量设置隐私</el-dropdown-item>
              <el-dropdown-item command="logout-sessions">❌ 批量退出其他设备</el-dropdown-item>
              <el-dropdown-item command="export">📥 批量导出账户数据</el-dropdown-item>
              <el-dropdown-item command="settings">✏️ 批量修改账户参数</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </transition>
</template>

<script setup>
defineProps({
  selectedCount: { type: Number, default: 0 },
  total: { type: Number, default: 0 },
})

const emit = defineEmits(['clear-selection', 'action'])
</script>

<style scoped>
.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background-color: rgba(64, 158, 255, 0.1);
  border: 1px solid rgba(64, 158, 255, 0.3);
  border-radius: var(--border-radius);
  margin-bottom: 12px;
}

.selected-info {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: var(--color-text);
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.2s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
