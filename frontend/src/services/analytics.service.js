// ANALYTICS SERVICE — daily rows for the charts and CSV export (F19, uses B18).
// GET /api/analytics/export: one row per sensor and day, scoped to the
// user's organization. format=json feeds the charts; format=csv downloads.

import adapter from './adapter.js'

const EXPORT_URL = '/api/analytics/export'

const analyticsService = {
  // range = { from, to } as ISO strings
  getDailyRows(range) {
    return adapter.get(EXPORT_URL, { params: { format: 'json', ...range } })
  },

  // Returns the CSV as a Blob; the caller triggers the download.
  exportCsv(range) {
    return adapter.get(EXPORT_URL, {
      params: { format: 'csv', ...range },
      responseType: 'blob',
    })
  },
}

export default analyticsService
