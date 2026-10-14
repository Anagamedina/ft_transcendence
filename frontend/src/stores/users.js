import { defineStore } from 'pinia'
import { ref } from 'vue'
import usersService from '../services/users.service.js'

export const useUsersStore = defineStore('users', () => {
  const items = ref([])
  const currentUser = ref(null)
  const page = ref(1)
  const pageSize = ref(20)
  const total = ref(0)
  const pages = ref(0)
  const status = ref('idle')
  const error = ref(null)

  async function fetchUsers(params = {}) {
    status.value = 'loading'
    error.value = null

    try {
      const response = await usersService.getUsers(params)
      const data = response.data

      items.value = data.items ?? []
      page.value = data.page ?? params.page ?? 1
      pageSize.value = data.page_size ?? params.page_size ?? 20
      total.value = data.total ?? items.value.length
      pages.value = data.pages ?? 0
      status.value = 'success'

      return data
    } catch (err) {
      error.value = err.message ?? 'Unable to load users.'
      status.value = 'error'
      throw err
    }
  }

  async function fetchUser(id) {
    status.value = 'loading'
    error.value = null

    try {
      const response = await usersService.getUser(id)
      currentUser.value = response.data
      status.value = 'success'
      return currentUser.value
    } catch (err) {
      error.value = err.message ?? 'Unable to load the user.'
      status.value = 'error'
      throw err
    }
  }

  async function createUser(data) {
    error.value = null

    try {
      const response = await usersService.createUser(data)
      const created = response.data

      items.value = [created, ...items.value]
      return created
    } catch (err) {
      error.value = err.message ?? 'Unable to create the user.'
      throw err
    }
  }

  async function updateUser(id, data) {
    error.value = null

    try {
      const response = await usersService.updateUser(id, data)
      const updated = response.data

      items.value = items.value.map((item) =>
        item.id === id ? updated : item,
      )

      if (currentUser.value?.id === id) {
        currentUser.value = updated
      }

      return updated
    } catch (err) {
      error.value = err.message ?? 'Unable to update the user.'
      throw err
    }
  }

  async function deleteUser(id) {
    error.value = null

    try {
      await usersService.deleteUser(id)
      items.value = items.value.filter((item) => item.id !== id)

      if (currentUser.value?.id === id) {
        currentUser.value = null
      }
    } catch (err) {
      error.value = err.message ?? 'Unable to delete the user.'
      throw err
    }
  }

  function reset() {
    items.value = []
    currentUser.value = null
    page.value = 1
    pageSize.value = 20
    total.value = 0
    pages.value = 0
    status.value = 'idle'
    error.value = null
  }

  return {
    items,
    currentUser,
    page,
    pageSize,
    total,
    pages,
    status,
    error,
    fetchUsers,
    fetchUser,
    createUser,
    updateUser,
    deleteUser,
    reset,
  }
})