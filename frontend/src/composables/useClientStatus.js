// Translates a client's technical status (OrganizationResponse.status + trial_ends_at)
// into what the admin sees: label, pill colors and the trial text.
// Centralized here so the clients table and the client detail page always show
// the same thing. It never changes data; it only translates what the mock or API sends.

const DAY_MS = 24 * 60 * 60 * 1000

// "Trial ended" is not a backend status: it is TRIAL with trial_ends_at in the past.
// TRIAL_ENDED is a frontend-only key used to pick its label and colors.
const STATUS_MAP = {
  TRIAL: { label: 'En prueba', pillClass: 'bg-blue-100 text-blue-800' },
  TRIAL_ENDED: { label: 'Prueba terminada', pillClass: 'bg-amber-100 text-amber-800' },
  ACTIVE: { label: 'Activo', pillClass: 'bg-emerald-100 text-emerald-800' },
  SUSPENDED: { label: 'Suspendido', pillClass: 'bg-slate-200 text-slate-700' },
}

// Fallback so an unexpected status never breaks the table
const UNKNOWN_STATUS = { label: 'Desconocido', pillClass: 'bg-gray-100 text-gray-700' }

// Short Spanish date, e.g. "8 oct"
const shortDate = new Intl.DateTimeFormat('es-ES', { day: 'numeric', month: 'short' })

// Same date at 00:00, so day differences ignore the hour
function startOfDay(date) {
  const day = new Date(date)
  day.setHours(0, 0, 0, 0)
  return day
}

// Calendar days from today until the trial ends (0 = today, 1 = tomorrow)
function daysUntil(endDate, now) {
  // Math.round absorbs the 23h/25h days of daylight saving changes
  return Math.round((startOfDay(endDate) - startOfDay(now)) / DAY_MS)
}

// Text for the "Prueba" column: remaining days, end date or a dash
function trialText(client, now) {
  if (client.status !== 'TRIAL' || !client.trial_ends_at) return '—'

  const endDate = new Date(client.trial_ends_at)
  if (endDate <= now) return `Terminó el ${shortDate.format(endDate)}`

  const days = daysUntil(endDate, now)
  if (days === 0) return 'Termina hoy'
  if (days === 1) return 'Termina mañana'
  return `Quedan ${days} días`
}

// Main helper. `now` is a parameter only so it can be tested with a fixed date.
export function useClientStatus(client, now = new Date()) {
  const trialEnded =
    client.status === 'TRIAL' &&
    Boolean(client.trial_ends_at) &&
    new Date(client.trial_ends_at) <= now

  const key = trialEnded ? 'TRIAL_ENDED' : client.status
  const { label, pillClass } = STATUS_MAP[key] || UNKNOWN_STATUS

  return { label, pillClass, trialEnded, trialText: trialText(client, now) }
}