import { defineStore } from 'pinia'
import { ref } from 'vue'
import { tasksApi } from '../api/index.js'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref([])
  const loading = ref(false)
  const activeTask = ref(null)

  async function fetchTasks(params = {}) {
    loading.value = true
    try {
      const data = await tasksApi.getAll(params)
      tasks.value = data
    } catch (err) {
      console.error('Failed to fetch tasks:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchRecentTasks(limit = 5) {
    try {
      const data = await tasksApi.getRecent(limit)
      return data
    } catch (err) {
      console.error('Failed to fetch recent tasks:', err)
      return []
    }
  }

  async function startTask(id) {
    const result = await tasksApi.start(id)
    const task = tasks.value.find(t => t.id === id)
    if (task) task.status = 'running'
    return result
  }

  async function pauseTask(id) {
    const result = await tasksApi.pause(id)
    const task = tasks.value.find(t => t.id === id)
    if (task) task.status = 'paused'
    return result
  }

  async function stopTask(id) {
    const result = await tasksApi.stop(id)
    const task = tasks.value.find(t => t.id === id)
    if (task) task.status = 'stopped'
    return result
  }

  async function deleteTask(id) {
    await tasksApi.delete(id)
    tasks.value = tasks.value.filter(t => t.id !== id)
  }

  return {
    tasks,
    loading,
    activeTask,
    fetchTasks,
    fetchRecentTasks,
    startTask,
    pauseTask,
    stopTask,
    deleteTask,
  }
})
