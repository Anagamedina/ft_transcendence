// STORE analytics — date range, daily rows and the series of the charts (F19).
//
// One request feeds everything: GET /api/analytics/export?format=json returns
// one row per sensor and day (alerts and aggregated readings), already
// filtered by the user's organization. KPIs and charts are computed here.
//
// Dates: the inputs hold inclusive days (YYYY-MM-DD). The API range is
// half-open [from, to), so `to` is sent as the day after. Days are UTC, the
// same as the backend groups them.

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import analyticsService from '../services/analytics.service.js'

const DEFAULT_DAYS = 30
const MAX_DAYS = 366 // same limit as the backend (DateRangeParams.MAX_DAYS)

function isoDay(date) {
  return date.toISOString().slice(0, 10)
}

function addDays(day, n) {
  const date = new Date(`${day}T00:00:00Z`)
  date.setUTCDate(date.getUTCDate() + n)
  return isoDay(date)
}

function sumBy(rows, key, field) {
  const totals = new Map()
  for (const row of rows) {
    totals.set(row[key], (totals.get(row[key]) ?? 0) + row[field])
  }
  return totals
}

export const useAnalyticsStore = defineStore('analytics', () => {
  // STATE
  const today = isoDay(new Date())
  const fromDate = ref(addDays(today, -(DEFAULT_DAYS - 1)))
  const toDate = ref(today)
  const rows = ref([])
  const status = ref('idle') // idle | loading | success | error
  const error = ref(null)
  const lastUpdated = ref(null)
  const exporting = ref(false)
  let requestId = 0 // ignores responses of a range that is no longer selected

  // GETTERS
  const rangeError = computed(() => {
    if (!fromDate.value || !toDate.value) return 'Elige las dos fechas.'
    if (fromDate.value > toDate.value) return 'La fecha de inicio tiene que ser anterior a la de fin.'
    const days = (new Date(toDate.value) - new Date(fromDate.value)) / 86400000 + 1
    if (days > MAX_DAYS) return `El periodo no puede pasar de ${MAX_DAYS} días.`
    return null
  })

  // Range as the API expects it: `to` exclusive.
  const apiRange = computed(() => ({ from: fromDate.value, to: addDays(toDate.value, 1) }))

  // Every day of the range, so days without alerts show as 0 on the line.
  const days = computed(() => {
    if (rangeError.value) return []
    const list = []
    for (let d = fromDate.value; d <= toDate.value; d = addDays(d, 1)) list.push(d)
    return list
  })

  const alertsByDay = computed(() => {
    const totals = sumBy(rows.value, 'date', 'alerts_total')
    const critical = sumBy(rows.value, 'date', 'alerts_critical')
    return {
      labels: days.value,
      total: days.value.map((d) => totals.get(d) ?? 0),
      critical: days.value.map((d) => critical.get(d) ?? 0),
    }
  })

  // `by` = 'organization' (one bar per client) or 'sensor_name'
  function alertsBy(by) {
    const totals = [...sumBy(rows.value, by, 'alerts_total')]
      .filter(([, n]) => n > 0)
      .sort((a, b) => b[1] - a[1])
    return { labels: totals.map(([k]) => k), values: totals.map(([, n]) => n) }
  }

  const totalAlerts = computed(() => rows.value.reduce((n, r) => n + r.alerts_total, 0))
  const criticalAlerts = computed(() => rows.value.reduce((n, r) => n + r.alerts_critical, 0))
  const resolvedAlerts = computed(() => rows.value.reduce((n, r) => n + r.alerts_resolved, 0))
  const totalReadings = computed(() => rows.value.reduce((n, r) => n + r.readings_count, 0))
  const resolvedPercent = computed(() =>
    totalAlerts.value ? Math.round((resolvedAlerts.value / totalAlerts.value) * 100) : null
  )
  const alertsBySeverity = computed(() => ({
    labels: ['Aviso (WARNING)', 'Crítica (CRITICAL)'],
    values: [totalAlerts.value - criticalAlerts.value, criticalAlerts.value],
  }))

  // ACTIONS
  // background = periodic refresh: keeps the current data on screen instead
  // of showing the loading state, and keeps it if the refresh fails.
  async function fetchRows({ background = false } = {}) {
    if (rangeError.value) return
    const id = ++requestId
    if (!background) {
      status.value = 'loading'
      error.value = null
    }
    try {
      const response = await analyticsService.getDailyRows(apiRange.value)
      if (id !== requestId) return
      rows.value = response.data
      status.value = 'success'
      error.value = null
      lastUpdated.value = new Date()
    } catch (err) {
      if (id !== requestId) return
      error.value = { code: err.code, message: err.message, details: err.details }
      if (!background) {
        rows.value = []
        status.value = 'error'
      }
    }
  }

  function setRange(from, to) {
    fromDate.value = from
    toDate.value = to
    return fetchRows()
  }

  function setLastDays(n) {
    const end = isoDay(new Date())
    return setRange(addDays(end, -(n - 1)), end)
  }

  async function exportCsv() {
    if (rangeError.value) return
    exporting.value = true
    try {
      const response = await analyticsService.exportCsv(apiRange.value)
      const disposition = response.headers?.['content-disposition'] ?? ''
      const filename =
        /filename="([^"]+)"/.exec(disposition)?.[1] ??
        `aquaguard-analytics_${apiRange.value.from}_${apiRange.value.to}.csv`
      const url = URL.createObjectURL(response.data)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      link.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      error.value = { code: err.code, message: err.message, details: err.details }
    } finally {
      exporting.value = false
    }
  }

  return {
    fromDate,
    toDate,
    rows,
    status,
    error,
    lastUpdated,
    exporting,

    rangeError,
    alertsByDay,
    alertsBy,
    alertsBySeverity,
    totalAlerts,
    criticalAlerts,
    resolvedPercent,
    totalReadings,

    fetchRows,
    setRange,
    setLastDays,
    exportCsv,
  }
})
