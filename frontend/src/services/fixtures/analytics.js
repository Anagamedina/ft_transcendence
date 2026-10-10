// Fixtures mock of GET /api/analytics/export (F19).
// Shape conforms to DailyRow: one row per sensor and day.
// Generated for any range so the charts have data in mock mode; the values
// are pseudo-random but stable for a given day and sensor.

import { sensors } from './sensors.js'
import { sites } from './sites.js'

const ORGANIZATIONS = {
  'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa': 'Hotel Diagonal Mar',
  'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb': 'Escola Gràcia',
  'cccccccc-cccc-4ccc-8ccc-cccccccccccc': 'Comunitat de veïns Sants',
}

// Small deterministic hash -> [0, 1)
function noise(seed) {
  let h = 2166136261
  for (const ch of seed) h = Math.imul(h ^ ch.charCodeAt(0), 16777619)
  return ((h >>> 0) % 1000) / 1000
}

export function dailyRows(from, to) {
  const rows = []
  const day = new Date(from)
  day.setUTCHours(0, 0, 0, 0)
  const end = new Date(to)

  while (day < end) {
    const date = day.toISOString().slice(0, 10)
    for (const sensor of sensors) {
      const site = sites.find((s) => s.id === sensor.site_id)
      const n = noise(`${date}:${sensor.id}`)
      const alerts = n > 0.7 ? Math.round(n * 3) : 0
      const critical = alerts && n > 0.9 ? 1 : 0
      rows.push({
        date,
        organization: ORGANIZATIONS[site?.organization_id] ?? 'Sin organización',
        site: site?.name ?? '—',
        sensor_id: sensor.id,
        sensor_external_id: sensor.id.slice(0, 8),
        sensor_name: sensor.name,
        unit: 'bar',
        readings_count: 24,
        pressure_min: +(2.5 + n).toFixed(3),
        pressure_avg: +(3.5 + n / 2).toFixed(3),
        pressure_max: +(4.5 + n).toFixed(3),
        alerts_total: alerts,
        alerts_critical: critical,
        alerts_resolved: Math.max(alerts - 1, 0),
      })
    }
    day.setUTCDate(day.getUTCDate() + 1)
  }
  return rows
}
