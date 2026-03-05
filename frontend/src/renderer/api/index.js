import axios from 'axios'
import logger from '../utils/logger.js'

const BASE_URL = 'http://45.77.121.38:8000'

const http = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
http.interceptors.request.use(
  config => {
    logger.info(`📤 API 请求: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  err => {
    logger.error('❌ API 请求错误', err.message)
    return Promise.reject(err)
  }
)

// 响应拦截器
http.interceptors.response.use(
  res => {
    logger.success(`✅ API 响应: ${res.config.url}`)
    return res.data
  },
  err => {
    const message = err.response?.data?.detail || err.message || '请求失败'
    logger.error(`❌ API 错误: ${message}`, {
      url: err.config?.url,
      status: err.response?.status,
      data: err.response?.data
    })
    return Promise.reject(new Error(message))
  }
)

export const accountsApi = {
  getList: (params) => http.get('/api/accounts/', { params }),
  getOne: (id) => http.get(`/api/accounts/${id}`),
  create: (data) => http.post('/api/accounts/', data),
  update: (id, data) => http.put(`/api/accounts/${id}`, data),
  delete: (id) => http.delete(`/api/accounts/${id}`),
  bulkAction: (data) => http.post('/api/accounts/bulk-action', data),
  bulkCheckSpam: (data) => http.post('/api/accounts/bulk/check-spam', data),
  bulkSet2fa: (data) => http.post('/api/accounts/bulk/set-2fa', data),
  bulkUpdateProfile: (data) => http.post('/api/accounts/bulk/update-profile', data),
  import: (formData) => http.post('/api/accounts/import', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  importFiles: (formData, onProgress) => http.post('/api/accounts/import/files', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percentCompleted = progressEvent.loaded / progressEvent.total
        onProgress(percentCompleted)
      }
    }
  }),
  importSession: (data) => http.post('/api/accounts/import/session', data),
  export: () => http.get('/api/accounts/export'),
}

export const proxiesApi = {
  getList: (params) => http.get('/api/proxies/', { params }),
  create: (data) => http.post('/api/proxies/', data),
  update: (id, data) => http.put(`/api/proxies/${id}`, data),
  delete: (id) => http.delete(`/api/proxies/${id}`),
  test: (id) => http.post(`/api/proxies/${id}/test`),
  import: (data) => http.post('/api/proxies/import', data),
  autoAssign: (accountIds) => http.post('/api/proxies/auto-assign', accountIds),
}

export const messagesApi = {
  getTasks: (params) => http.get('/api/messages/tasks', { params }),
  createTask: (data) => http.post('/api/messages/tasks', data),
  updateTask: (id, data) => http.put(`/api/messages/tasks/${id}`, data),
  deleteTask: (id) => http.delete(`/api/messages/tasks/${id}`),
  startTask: (id) => http.post(`/api/messages/tasks/${id}/start`),
  pauseTask: (id) => http.post(`/api/messages/tasks/${id}/pause`),
  stopTask: (id) => http.post(`/api/messages/tasks/${id}/stop`),
  getGroups: (params) => http.get('/api/messages/groups', { params }),
  getTemplates: () => http.get('/api/messages/templates'),
  createTemplate: (data) => http.post('/api/messages/templates', data),
}

export const directApi = {
  getTasks: (params) => http.get('/api/direct/tasks', { params }),
  createTask: (data) => http.post('/api/direct/tasks', data),
  deleteTask: (id) => http.delete(`/api/direct/tasks/${id}`),
  getUsersFromGroup: (groupId, params) => http.get(`/api/direct/users/from-group/${groupId}`, { params }),
  importUsers: (users) => http.post('/api/direct/users/import', users),
  getLogs: (params) => http.get('/api/direct/logs', { params }),
}

export const invitesApi = {
  getTasks: (params) => http.get('/api/invites/tasks', { params }),
  createTask: (data) => http.post('/api/invites/tasks', data),
  deleteTask: (id) => http.delete(`/api/invites/tasks/${id}`),
  getGroups: () => http.get('/api/invites/groups'),
  checkPermissions: (params) => http.get('/api/invites/check-permissions', { params }),
  getLogs: (params) => http.get('/api/invites/logs', { params }),
}

export const checkerApi = {
  check: (data) => http.post('/api/checker/check', data),
  getStatus: (accountId) => http.get(`/api/checker/status/${accountId}`),
  getHealthScore: (accountId) => http.get(`/api/checker/health-score/${accountId}`),
  schedule: (data) => http.post('/api/checker/schedule', data),
  getReports: (params) => http.get('/api/checker/reports', { params }),
}

export const profileApi = {
  getBulk: (data) => http.post('/api/profile/get-bulk', data),
  updateBulk: (data) => http.post('/api/profile/update-bulk', data),
  getTemplates: () => http.get('/api/profile/templates'),
  createTemplate: (data) => http.post('/api/profile/templates', data),
  setPrivacy: (data) => http.post('/api/profile/privacy', data),
}

export const tasksApi = {
  getAll: (params) => http.get('/api/tasks/', { params }),
  getRecent: (limit) => http.get('/api/tasks/recent', { params: { limit } }),
  getOne: (id) => http.get(`/api/tasks/${id}`),
  start: (id) => http.post(`/api/tasks/${id}/start`),
  pause: (id) => http.post(`/api/tasks/${id}/pause`),
  stop: (id) => http.post(`/api/tasks/${id}/stop`),
  delete: (id) => http.delete(`/api/tasks/${id}`),
}

export const statsApi = {
  getOverview: () => http.get('/api/stats/overview'),
  getChartData: (days) => http.get('/api/stats/chart-data', { params: { days } }),
  getAccountStats: () => http.get('/api/stats/accounts'),
  getTaskStats: (days) => http.get('/api/stats/tasks', { params: { days } }),
  getPerformance: () => http.get('/api/stats/performance'),
  export: (params) => http.get('/api/stats/export', { params }),
}

export const settingsApi = {
  get: () => http.get('/api/settings/'),
  update: (data) => http.put('/api/settings/', data),
  testConnection: (data) => http.post('/api/settings/test-connection', data),
  backup: () => http.post('/api/settings/backup'),
  restore: (file) => http.post('/api/settings/restore', { backup_file: file }),
  clearLogs: (days) => http.post('/api/settings/clear-logs', null, { params: { days_to_keep: days } }),
}

export default http
