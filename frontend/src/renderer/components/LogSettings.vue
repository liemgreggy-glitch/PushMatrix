<template>
  <el-card class="log-settings">
    <template #header>
      <span>日志设置</span>
    </template>

    <el-form label-width="120px">
      <el-form-item label="API 日志">
        <el-switch v-model="config.api.enabled" @change="updateConfig" />
        <span class="hint">显示 API 请求/响应日志</span>
      </el-form-item>

      <el-form-item v-if="config.api.enabled" label="显示成功响应">
        <el-switch v-model="config.api.showSuccess" @change="updateConfig" />
        <span class="hint">成功的 API 响应也会显示</span>
      </el-form-item>

      <el-form-item label="业务日志">
        <el-switch v-model="config.business.enabled" @change="updateConfig" />
        <span class="hint">显示业务逻辑日志（导入、操作等）</span>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { reactive } from 'vue'
import logger from '../utils/logger'
import { ElMessage } from 'element-plus'

const config = reactive({
  api: {
    enabled: false,
    showSuccess: false,
  },
  business: {
    enabled: true,
  },
})

function updateConfig() {
  logger.setConfig(config)
  ElMessage.success('日志设置已更新')
}
</script>

<style scoped>
.log-settings {
  margin: 20px;
}

.hint {
  margin-left: 10px;
  font-size: 12px;
  color: #999;
}
</style>
