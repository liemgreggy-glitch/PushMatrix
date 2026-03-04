<template>
  <div class="page-container">
    <div class="page-header">
      <span class="page-title">资料管理</span>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="批量获取资料" name="get" />
      <el-tab-pane label="批量修改资料" name="update" />
      <el-tab-pane label="隐私设置" name="privacy" />
      <el-tab-pane label="资料模板" name="templates" />
    </el-tabs>

    <!-- Get Profiles -->
    <div v-if="activeTab === 'get'" class="tab-content">
      <el-card>
        <el-form label-width="120px">
          <el-form-item label="操作账号">
            <el-select v-model="getForm.account_id" style="width: 100%;">
              <el-option v-for="acc in mockAccounts" :key="acc.id" :label="acc.phone" :value="acc.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="来源">
            <el-radio-group v-model="getForm.source">
              <el-radio label="group">从群组获取</el-radio>
              <el-radio label="user_ids">指定用户 ID</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item v-if="getForm.source === 'group'" label="群组">
            <el-input v-model="getForm.group_id" placeholder="输入群组用户名或链接" />
          </el-form-item>
        </el-form>
        <el-button type="primary" :loading="loadingProfiles" @click="getProfiles">开始获取</el-button>
      </el-card>

      <el-table v-if="profiles.length" :data="profiles" style="width: 100%; margin-top: 16px;">
        <el-table-column label="用户ID" prop="user_id" width="120" />
        <el-table-column label="用户名" prop="username" min-width="140">
          <template #default="{ row }">@{{ row.username }}</template>
        </el-table-column>
        <el-table-column label="姓名" min-width="140">
          <template #default="{ row }">{{ row.first_name }} {{ row.last_name }}</template>
        </el-table-column>
        <el-table-column label="简介" prop="bio" min-width="200" />
      </el-table>
    </div>

    <!-- Update Profiles -->
    <div v-if="activeTab === 'update'" class="tab-content">
      <el-card>
        <el-form label-width="120px">
          <el-form-item label="目标账号">
            <el-select v-model="updateForm.account_ids" multiple style="width: 100%;">
              <el-option v-for="acc in mockAccounts" :key="acc.id" :label="acc.phone" :value="acc.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="名字">
            <el-input v-model="updateForm.updates.first_name" placeholder="留空则不修改" />
          </el-form-item>
          <el-form-item label="姓氏">
            <el-input v-model="updateForm.updates.last_name" placeholder="留空则不修改" />
          </el-form-item>
          <el-form-item label="简介">
            <el-input v-model="updateForm.updates.bio" type="textarea" :rows="3" placeholder="留空则不修改" />
          </el-form-item>
          <el-form-item label="用户名前缀">
            <el-input v-model="updateForm.updates.username_prefix" placeholder="会自动加编号，留空则不修改" />
          </el-form-item>
        </el-form>
        <el-button type="primary" :loading="updating" @click="updateProfiles">批量修改</el-button>
      </el-card>
    </div>

    <!-- Privacy Settings -->
    <div v-if="activeTab === 'privacy'" class="tab-content">
      <el-card>
        <el-form label-width="160px">
          <el-form-item label="目标账号">
            <el-select v-model="privacyForm.account_ids" multiple style="width: 100%;">
              <el-option v-for="acc in mockAccounts" :key="acc.id" :label="acc.phone" :value="acc.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="电话号码可见性">
            <el-select v-model="privacyForm.phone_visibility" style="width: 200px;">
              <el-option label="所有人" value="everybody" />
              <el-option label="联系人" value="contacts" />
              <el-option label="无人" value="nobody" />
            </el-select>
          </el-form-item>
          <el-form-item label="最后上线时间">
            <el-select v-model="privacyForm.last_seen" style="width: 200px;">
              <el-option label="所有人" value="everybody" />
              <el-option label="联系人" value="contacts" />
              <el-option label="无人" value="nobody" />
            </el-select>
          </el-form-item>
          <el-form-item label="个人资料照片">
            <el-select v-model="privacyForm.profile_photo" style="width: 200px;">
              <el-option label="所有人" value="everybody" />
              <el-option label="联系人" value="contacts" />
            </el-select>
          </el-form-item>
          <el-form-item label="转发消息隐私">
            <el-select v-model="privacyForm.forwards" style="width: 200px;">
              <el-option label="所有人" value="everybody" />
              <el-option label="联系人" value="contacts" />
              <el-option label="无人" value="nobody" />
            </el-select>
          </el-form-item>
        </el-form>
        <el-button type="primary" :loading="settingPrivacy" @click="setPrivacy">保存隐私设置</el-button>
      </el-card>
    </div>

    <!-- Templates -->
    <div v-if="activeTab === 'templates'" class="tab-content">
      <div class="page-header" style="margin-bottom: 16px;">
        <span />
        <el-button type="primary" icon="Plus" @click="showTemplateDialog = true">新建模板</el-button>
      </div>
      <el-table :data="templates" style="width: 100%">
        <el-table-column label="模板名称" prop="name" min-width="160" />
        <el-table-column label="名字" prop="first_name" min-width="120" />
        <el-table-column label="简介" prop="bio" min-width="200" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" icon="Check" @click="applyTemplate(row)">应用</el-button>
            <el-button size="small" icon="Delete" type="danger" />
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Template Dialog -->
    <el-dialog v-model="showTemplateDialog" title="新建资料模板" width="400px">
      <el-form :model="templateForm" label-width="100px">
        <el-form-item label="模板名称" required>
          <el-input v-model="templateForm.name" />
        </el-form-item>
        <el-form-item label="名字">
          <el-input v-model="templateForm.first_name" />
        </el-form-item>
        <el-form-item label="姓氏">
          <el-input v-model="templateForm.last_name" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="templateForm.bio" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTemplateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTemplate">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { profileApi } from '../api/index.js'

const activeTab = ref('get')
const loadingProfiles = ref(false)
const updating = ref(false)
const settingPrivacy = ref(false)
const showTemplateDialog = ref(false)
const profiles = ref([])
const templates = ref([])
const mockAccounts = [{ id: 1, phone: '+1234567890' }, { id: 2, phone: '+0987654321' }]

const getForm = ref({ account_id: 1, source: 'group', group_id: '' })
const updateForm = ref({ account_ids: [], updates: { first_name: '', last_name: '', bio: '', username_prefix: '' } })
const privacyForm = ref({ account_ids: [], phone_visibility: 'contacts', last_seen: 'contacts', profile_photo: 'everybody', forwards: 'everybody' })
const templateForm = ref({ name: '', first_name: '', last_name: '', bio: '' })

async function getProfiles() {
  loadingProfiles.value = true
  try {
    const result = await profileApi.getBulk(getForm.value)
    profiles.value = result.profiles
  } catch (err) {
    ElMessage.error('获取失败')
  } finally {
    loadingProfiles.value = false
  }
}

async function updateProfiles() {
  updating.value = true
  try {
    await profileApi.updateBulk(updateForm.value)
    ElMessage.success('资料批量修改成功')
  } catch (err) {
    ElMessage.error('修改失败')
  } finally {
    updating.value = false
  }
}

async function setPrivacy() {
  settingPrivacy.value = true
  try {
    await profileApi.setPrivacy(privacyForm.value)
    ElMessage.success('隐私设置已保存')
  } catch (err) {
    ElMessage.error('设置失败')
  } finally {
    settingPrivacy.value = false
  }
}

async function saveTemplate() {
  try {
    const t = await profileApi.createTemplate(templateForm.value)
    templates.value.push(t)
    showTemplateDialog.value = false
    ElMessage.success('模板已创建')
  } catch (err) {
    ElMessage.error('创建失败')
  }
}

function applyTemplate(template) {
  updateForm.value.updates = { ...template }
  activeTab.value = 'update'
  ElMessage.info('模板已应用到修改资料页')
}

onMounted(async () => {
  templates.value = await profileApi.getTemplates().catch(() => [])
})
</script>

<style scoped>
.tab-content { margin-top: 20px; }
</style>
