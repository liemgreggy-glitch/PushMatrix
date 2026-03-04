import { defineStore } from 'pinia'
import { ref } from 'vue'
import { accountsApi } from '../api/index.js'

export const useAccountStore = defineStore('account', () => {
  const accounts = ref([])
  const groups = ref([])
  const loading = ref(false)
  const selectedIds = ref([])
  const total = ref(0)

  async function fetchAccounts(params = {}) {
    loading.value = true
    try {
      const data = await accountsApi.getList(params)
      accounts.value = data
      total.value = data.length
    } catch (err) {
      console.error('Failed to fetch accounts:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchGroups() {
    try {
      const data = await accountsApi.getGroups()
      groups.value = data
    } catch (err) {
      console.error('Failed to fetch groups:', err)
    }
  }

  async function deleteAccount(id) {
    await accountsApi.delete(id)
    accounts.value = accounts.value.filter(a => a.id !== id)
    total.value--
  }

  async function bulkAction(actionType, ids, params = {}) {
    return await accountsApi.bulkAction({ action_type: actionType, account_ids: ids, params })
  }

  function toggleSelection(id) {
    const idx = selectedIds.value.indexOf(id)
    if (idx === -1) {
      selectedIds.value.push(id)
    } else {
      selectedIds.value.splice(idx, 1)
    }
  }

  function clearSelection() {
    selectedIds.value = []
  }

  function selectAll() {
    selectedIds.value = accounts.value.map(a => a.id)
  }

  return {
    accounts,
    groups,
    loading,
    selectedIds,
    total,
    fetchAccounts,
    fetchGroups,
    deleteAccount,
    bulkAction,
    toggleSelection,
    clearSelection,
    selectAll,
  }
})
