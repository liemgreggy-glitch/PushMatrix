<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">批量导入账号</span>
    </div>

    <el-row :gutter="16">
      <el-col :span="14">
        <el-card>
          <template #header><span>选择导入方式</span></template>

          <el-tabs v-model="importMethod">
            <el-tab-pane label="文件导入" name="file">
              <div class="upload-area">
                <el-upload
                  drag
                  action="#"
                  :auto-upload="false"
                  :on-change="handleFileChange"
                  accept=".xlsx,.csv,.txt"
                >
                  <el-icon size="40" color="#409EFF"><Upload /></el-icon>
                  <p class="upload-text">拖拽文件到此处，或点击上传</p>
                  <p class="upload-hint">支持 Excel (.xlsx)、CSV (.csv)、TXT (.txt) 格式</p>
                </el-upload>
              </div>
            </el-tab-pane>

            <el-tab-pane label="Session 导入" name="session">
              <el-form label-width="100px">
                <el-form-item label="Session 字符串">
                  <el-input
                    v-model="sessionInput"
                    type="textarea"
                    :rows="8"
                    placeholder="每行一个 Session 字符串"
                  />
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="手动输入" name="manual">
              <el-form label-width="100px">
                <el-form-item label="手机号列表">
                  <el-input
                    v-model="phoneInput"
                    type="textarea"
                    :rows="8"
                    placeholder="每行一个手机号，格式: +1234567890"
                  />
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>

          <div class="import-actions">
            <el-button icon="Download" @click="downloadTemplate">下载模板</el-button>
            <el-button type="primary" icon="Upload" @click="startImport" :loading="importing">
              开始导入
            </el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card>
          <template #header><span>导入结果</span></template>
          <div v-if="!importResult" class="empty-import">
            <el-empty description="等待导入..." :image-size="80" />
          </div>
          <div v-else class="import-result">
            <div class="result-item success">
              <el-icon color="#A6E3A1"><CircleCheck /></el-icon>
              <span>成功: {{ importResult.imported }}</span>
            </div>
            <div class="result-item danger">
              <el-icon color="#F38BA8"><CircleClose /></el-icon>
              <span>失败: {{ importResult.failed }}</span>
            </div>
            <div v-if="importResult.errors?.length" class="error-list">
              <p class="error-title">错误详情:</p>
              <div v-for="(err, i) in importResult.errors" :key="i" class="error-item">
                {{ err }}
              </div>
            </div>
          </div>
        </el-card>

        <el-card style="margin-top: 16px;">
          <template #header><span>导入说明</span></template>
          <ul class="import-tips">
            <li>Excel/CSV 格式：第一列为手机号，第二列为 Session（可选）</li>
            <li>TXT 格式：每行一个手机号或 Session</li>
            <li>手机号格式：+国家代码+号码，如 +8613800138000</li>
            <li>Session 格式：Pyrogram 或 Telethon Session 字符串</li>
            <li>批量导入上限：单次最多 500 个账号</li>
          </ul>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { accountsApi } from '../../api/index.js'

const importMethod = ref('file')
const sessionInput = ref('')
const phoneInput = ref('')
const importing = ref(false)
const importResult = ref(null)
const selectedFile = ref(null)

function handleFileChange(file) {
  selectedFile.value = file.raw
}

async function startImport() {
  importing.value = true
  try {
    let result
    if (importMethod.value === 'file' && selectedFile.value) {
      const formData = new FormData()
      formData.append('file', selectedFile.value)
      result = await accountsApi.import(formData)
    } else {
      // TODO: handle session/manual import
      result = { imported: 0, failed: 0 }
    }
    importResult.value = result
    ElMessage.success(`导入完成：成功 ${result.imported} 个`)
  } catch (err) {
    ElMessage.error('导入失败: ' + err.message)
  } finally {
    importing.value = false
  }
}

function downloadTemplate() {
  ElMessage.info('模板下载功能即将可用')
}
</script>

<style scoped>
.upload-area {
  margin-bottom: 20px;
}

.upload-text {
  font-size: 14px;
  color: var(--color-text);
  margin-top: 8px;
}

.upload-hint {
  font-size: 12px;
  color: var(--color-text-muted);
}

.import-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  margin-bottom: 12px;
}

.error-list {
  margin-top: 12px;
  padding: 12px;
  background-color: var(--color-bg);
  border-radius: var(--border-radius);
}

.error-title {
  font-size: 13px;
  color: var(--color-text-muted);
  margin-bottom: 8px;
}

.error-item {
  font-size: 12px;
  color: var(--color-danger);
  padding: 2px 0;
}

.import-tips {
  padding-left: 20px;
  color: var(--color-text-muted);
  font-size: 13px;
  line-height: 1.8;
}

.empty-import {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}
</style>
