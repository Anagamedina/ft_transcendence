// USE FORMAT
// One place for dates and numbers shown in the interface (Spanish, es-ES).
// The API sends dates in UTC; the browser shows them in the user's local time.
//
// Usage:
//   const { formatDateTime, formatNumber } = useFormat()
//   formatDateTime('2026-10-14T06:20:00Z')   // 'hoy 08:20' (in Madrid)
//   formatDateTime('2026-10-13T15:05:00Z')   // 'ayer 17:05'
//   formatDateTime('2026-09-08T08:20:00Z')   // '8 sept 10:20'
//   formatDate('2026-10-21T10:00:00Z')       // '21 oct 2026'
//   formatNumber(1234.5)                     // '1234,5'
//   formatPressure(4.2)                      // '4,2 bar'

const LOCALE = 'es-ES'

const timeFormat = new Intl.DateTimeFormat(LOCALE, { hour: '2-digit', minute: '2-digit' })
const dayMonthFormat = new Intl.DateTimeFormat(LOCALE, { day: 'numeric', month: 'short' })
const fullDateFormat = new Intl.DateTimeFormat(LOCALE, { day: 'numeric', month: 'short', year: 'numeric' })
const relativeFormat = new Intl.RelativeTimeFormat(LOCALE, { numeric: 'always', style: 'short' })

// Number formatters are cached by number of decimals
const numberFormats = new Map()
function numberFormat(decimals) {
  const key = decimals ?? 'auto'
  if (!numberFormats.has(key)) {
    const options = decimals === undefined
      ? { maximumFractionDigits: 2 }
      : { minimumFractionDigits: decimals, maximumFractionDigits: decimals }
    numberFormats.set(key, new Intl.NumberFormat(LOCALE, options))
  }
  return numberFormats.get(key)
}

// ISO date with a time but no zone ('2026-10-14T06:20:00'): the API means UTC,
// but JavaScript would read it as local time, so a 'Z' is added.
const NO_ZONE = /T\d{2}:\d{2}(:\d{2}(\.\d+)?)?$/

// Date | string | number -> Date, or null when empty or not a valid date
export function parseDate(value) {
  if (value === null || value === undefined || value === '') return null
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value
  const text = typeof value === 'string' && NO_ZONE.test(value) ? `${value}Z` : value
  const date = new Date(text)
  return Number.isNaN(date.getTime()) ? null : date
}

// Calendar days between two dates in local time (0 = same day, 1 = yesterday)
function daysBetween(date, now) {
  const start = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  // Math.round absorbs the 23 h / 25 h days of daylight saving changes
  return Math.round((today - start) / 86400000)
}

// 'hoy 08:20', 'ayer 17:05', '8 sept 10:20', '8 sept 2025 10:20'
export function formatDateTime(value, { empty = '—', now = new Date() } = {}) {
  const date = parseDate(value)
  if (!date) return empty
  const time = timeFormat.format(date)
  const days = daysBetween(date, now)
  if (days === 0) return `hoy ${time}`
  if (days === 1) return `ayer ${time}`
  const format = date.getFullYear() === now.getFullYear() ? dayMonthFormat : fullDateFormat
  return `${format.format(date)} ${time}`
}

// '21 oct 2026'
export function formatDate(value, { empty = '—' } = {}) {
  const date = parseDate(value)
  return date ? fullDateFormat.format(date) : empty
}

// '21 oct'
export function formatShortDate(value, { empty = '—' } = {}) {
  const date = parseDate(value)
  return date ? dayMonthFormat.format(date) : empty
}

// '08:20'
export function formatTime(value, { empty = '—' } = {}) {
  const date = parseDate(value)
  return date ? timeFormat.format(date) : empty
}

// 'Ahora', 'hace 5 min', 'hace 3 h', 'hace 2 días'
export function formatRelative(value, { empty = '—', now = new Date() } = {}) {
  const date = parseDate(value)
  if (!date) return empty
  const seconds = Math.round((date.getTime() - now.getTime()) / 1000)
  if (seconds > -60) return 'Ahora'
  if (seconds > -3600) return relativeFormat.format(Math.round(seconds / 60), 'minute')
  if (seconds > -86400) return relativeFormat.format(Math.round(seconds / 3600), 'hour')
  return relativeFormat.format(Math.round(seconds / 86400), 'day')
}

// '1234,5' (decimals fixed when given, up to 2 otherwise)
export function formatNumber(value, decimals, { empty = '—' } = {}) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return empty
  return numberFormat(decimals).format(Number(value))
}

// '4,2 bar'
export function formatPressure(value, unit = 'bar', { empty = '—' } = {}) {
  const number = formatNumber(value, 1, { empty: null })
  return number === null ? empty : `${number} ${unit || 'bar'}`
}

// '2,0–6,0 bar'
export function formatRange(min, max, unit = 'bar') {
  return `${formatNumber(min, 1)}–${formatNumber(max, 1)} ${unit || 'bar'}`
}

export function useFormat() {
  return {
    parseDate,
    formatDateTime,
    formatDate,
    formatShortDate,
    formatTime,
    formatRelative,
    formatNumber,
    formatPressure,
    formatRange,
  }
}
