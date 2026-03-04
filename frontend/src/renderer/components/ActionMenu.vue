<template>
  <el-dropdown trigger="click" @command="handleCommand">
    <el-button type="primary">
      操作行动 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="check-spam">检查账户是否已拦截垃圾邮件</el-dropdown-item>
        <el-dropdown-item command="open-web">在网页上打开</el-dropdown-item>
        <el-dropdown-item command="2fa" divided>更改双重验证...</el-dropdown-item>
        <el-dropdown-item command="role-swap">角色互换...</el-dropdown-item>
        <el-dropdown-item command="fill-profile" divided>填写您的个人资料</el-dropdown-item>
        <el-dropdown-item command="edit-profile">编辑个人资料...</el-dropdown-item>
        <el-dropdown-item command="privacy">更改隐私设置...</el-dropdown-item>
        <el-dropdown-item command="close-sessions" divided>关闭第三方会话</el-dropdown-item>
        <el-dropdown-item command="download-info">下载账户信息</el-dropdown-item>
        <el-dropdown-item command="account-settings">更改账户设置...</el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { ElMessage } from 'element-plus'

const props = defineProps({
  selectedAccounts: { type: Array, default: () => [] },
})

const emit = defineEmits(['action'])

function handleCommand(command) {
  if (!props.selectedAccounts.length) {
    ElMessage.warning('请先选择账号')
    return
  }
  emit('action', command, props.selectedAccounts)
}
</script>
