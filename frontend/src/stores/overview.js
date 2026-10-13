// STORE overview — KPI cards of the dashboard (F12, uses B9).

import { defineStore } from 'pinia'
import { ref } from 'vue'
import analyticsService from '../services/analytics.service.js'

export const useOverviewStore = defineStore('overview', () => {
  // STATE
  const overview = ref(null)
  const status = ref('idle')
  const error = ref(null)

  // ACTIONS
  async function fetchOverview() {
    status.value = 'loading'
    error.value = null

    try {
      const response = await analyticsService.getOverview()

      overview.value = response.data
      status.value = 'success'

      return overview.value
    } catch (err) {
      overview.value = null
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
    overview,
    status,
    error,
    fetchOverview,
  }
})
