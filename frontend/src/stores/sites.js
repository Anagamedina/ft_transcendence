// STORE sites — list of sites from the API.

import { defineStore } from 'pinia'
import { ref } from 'vue'
import siteService from '../services/site.service.js'

export const useSitesStore = defineStore('sites', () => {
  // STATE
  const sites = ref([])
  const status = ref('idle')
  const error = ref(null)

  // ACTIONS
  async function fetchSites() {
    status.value = 'loading'
    error.value = null

    try {
      const response = await siteService.getSites()

      sites.value = response.data.items
      status.value = 'success'

      return sites.value
    } catch (err) {
      sites.value = []
      error.value = {
        code: err.code,
        message: err.message,
        details: err.details,
      }
      status.value = 'error'

      throw err
    }
  }

  return {
    sites,
    status,
    error,
    fetchSites,
  }
})
