<template>
  <el-table
    v-loading="loading"
    :data="accounts"
    style="width: 100%"
    row-key="id"
    @selection-change="handleSelectionChange"
  >
    <el-table-column type="selection" width="50" />
    <el-table-column label="手机号" prop="phone" min-width="140">
      <template #default="{ row }">
        <div class="account-phone">
          <el-avatar :size="28" class="account-avatar">
            {{ row.first_name?.[0] || row.phone[1] }}
          </el-avatar>
          <span>{{ row.phone }}</span>
        </div>
      </template>
    </el-table-column>
    <el-table-column label="用户名" prop="username" min-width="120">
      <template #default="{ row }">
        <span class="text-muted">{{ row.username ? `@${row.username}` : '-' }}</span>
      </template>
    </el-table-column>
    <el-table-column label="状态" prop="status" width="100">
      <template #default="{ row }">
        <el-tag :type="statusType(row.status)" size="small">
          {{ statusLabel(row.status) }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column label="健康度" prop="health_score" width="120">
      <template #default="{ row }">
        <el-progress
          :percentage="row.health_score"
          :color="healthColor(row.health_score)"
          :stroke-width="6"
          :show-text="false"
        />
        <span class="health-score">{{ row.health_score }}%</span>
      </template>
    </el-table-column>
    <el-table-column label="代理" prop="proxy_id" width="100">
      <template #default="{ row }">
        <span class="text-muted">{{ row.proxy_id ? `代理 #${row.proxy_id}` : '无' }}</span>
      </template>
    </el-table-column>
    <el-table-column label="标签" min-width="120">
      <template #default="{ row }">
        <el-tag
          v-for="tag in (row.tags || [])"
          :key="tag"
          size="small"
          class="tag-item"
        >
          {{ tag }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column label="操作" width="80" fixed="right">
      <template #default="{ row }">
        <el-dropdown trigger="click" @command="(cmd) => emit('row-action', cmd, row)">
          <el-button circle icon="MoreFilled" size="small" />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="start">启动账户</el-dropdown-item>
              <el-dropdown-item command="open-web">在浏览器打开</el-dropdown-item>
              <el-dropdown-item command="edit">编辑账号信息</el-dropdown-item>
              <el-dropdown-item command="2fa">修改 2FA</el-dropdown-item>
              <el-dropdown-item command="export-session">导出 Session</el-dropdown-item>
              <el-dropdown-item command="delete" divided class="danger-item">删除账号</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
defineProps({
  accounts: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['selection-change', 'row-action'])

function handleSelectionChange(selection) {
  emit('selection-change', selection)
}

function statusType(status) {
  const map = { online: 'success', offline: 'info', frozen: 'warning', spam: 'danger' }
  return map[status] || 'info'
}

function statusLabel(status) {
  const map = { online: '在线', offline: '离线', frozen: '冻结', spam: '受限' }
  return map[status] || status
}

function healthColor(score) {
  if (score >= 80) return '#A6E3A1'
  if (score >= 50) return '#FAB387'
  return '#F38BA8'
}
</script>

<style scoped>
.account-phone {
  display: flex;
  align-items: center;
  gap: 8px;
}

.account-avatar {
  background-color: #313244;
  color: var(--color-text);
  font-size: 12px;
  flex-shrink: 0;
}

.health-score {
  font-size: 11px;
  color: var(--color-text-muted);
  margin-left: 4px;
}

.tag-item {
  margin-right: 4px;
  margin-bottom: 2px;
}

:deep(.danger-item) {
  color: var(--color-danger) !important;
}
</style>
