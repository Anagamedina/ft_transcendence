// STORE sites — buildings list, creation and edition through the API (B2).

import { defineStore } from 'pinia'
import { ref } from 'vue'
import siteService from '../services/site.service.js'

// The API returns at most 100 items per page
const PAGE_SIZE = 100

// Same error shape as the other stores: { code, message, details }
function toStoreError(err) {
  return {
    code: err?.code,
    message: err?.message,
    details: err?.details,
  }
}

export const useSitesStore = defineStore('sites', () => {
  // STATE
  const sites = ref([])
  // 'idle' | 'loading' | 'success' | 'error'
  const status = ref('idle')
  const error = ref(null)

  // ACTIONS

  // Loads every building. The admin sees all clients, so the store asks for
  // page after page until it has them all; DataTable filters and paginates locally.
  async function fetchSites() {
    status.value = 'loading'
    error.value = null

    try {
      const all = []
      let page = 1
      let pages = 1

      do {
        const response = await siteService.getSites({ page, page_size: PAGE_SIZE })
        all.push(...response.data.items)
        pages = response.data.pages
        page += 1
      } while (page <= pages)

      sites.value = all
      status.value = 'success'
      return sites.value
    } catch (err) {
      sites.value = []
      error.value = toStoreError(err)
      status.value = 'error'
      throw err
    }
  }

  // POST /api/sites. Adds the new building to the list and returns it.
  // Errors are thrown to the caller, so the form can show them without
  // turning the whole list into an error state.
  async function createSite(data) {
    const response = await siteService.createSite(data)
    sites.value = [...sites.value, response.data]
    return response.data
  }

  // PATCH /api/sites/{id}. Replaces the building in the list with the API answer.
  async function updateSite(id, data) {
    const response = await siteService.updateSite(id, data)
    sites.value = sites.value.map((site) => (site.id === id ? response.data : site))
    return response.data
  }

  function siteById(id) {
    return sites.value.find((site) => site.id === id) ?? null
  }

  return {
    sites,
    status,
    error,
    fetchSites,
    createSite,
    updateSite,
    siteById,
  }
})
