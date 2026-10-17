<!--
  WEEK ALERTS GRID
  Alerts of one building during a week, one row per sensor and one column per
  day (F8), with the cell colour growing with the count. F9-C reuses it.
  Pure visual component: it receives GET /api/analytics/alerts/weekly (B9)
  already loaded and emits "select" with the sensor id when a row is clicked.
  Shape: days = ['2026-10-12', …] (7, Monday first, UTC),
         rows = [{ sensor_id, sensor_name, floor, counts: [7 numbers] }].
  Usage:
    <WeekAlertsGrid :days="weekly.days" :rows="weekly.rows"
      :selected-id="selectedId" @select="selectedId = $event" />
-->

<template>
  <EmptyState
    v-if="!rows.length"
    icon="alert"
    title="Este edificio no tiene sensores"
    message="Cuando se instale un sensor, verás aquí sus alertas de la semana."
    compact
  />

  <div v-else class="overflow-x-auto">
    <table class="w-full min-w-[560px] border-separate border-spacing-1 text-sm">
      <caption class="sr-only">{{ caption }}</caption>
      <thead>
        <tr>
          <th scope="col" class="px-2 py-1 text-left text-xs font-semibold text-slate-500">Sensor</th>
          <th
            v-for="(day, index) in days"
            :key="day"
            scope="col"
            class="w-12 px-1 py-1 text-center text-xs font-semibold"
            :class="index === todayIndex ? 'text-aqua-700' : 'text-slate-500'"
          >
            <span class="block">{{ weekdayLabel(day) }}</span>
            <span class="block font-normal">{{ dayNumber(day) }}</span>
          </th>
          <th scope="col" class="w-14 px-1 py-1 text-center text-xs font-semibold text-slate-500">Total</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in sortedRows"
          :key="row.sensor_id"
          class="cursor-pointer"
          @click="$emit('select', row.sensor_id)"
        >
          <th scope="row" class="rounded-md px-2 py-1 text-left font-normal">
            <button
              type="button"
              class="text-left hover:underline"
              :class="row.sensor_id === selectedId ? 'font-bold text-aqua-700' : 'font-medium text-slate-800'"
              :aria-pressed="row.sensor_id === selectedId"
              @click.stop="$emit('select', row.sensor_id)"
            >
              {{ row.sensor_name }}
            </button>
            <span class="block text-xs text-slate-500">{{ floorLabel(row.floor ?? 0) }}</span>
          </th>
          <td
            v-for="(count, index) in row.counts"
            :key="days[index] ?? index"
            class="h-10 rounded-md text-center font-semibold tabular-nums"
            :class="cellClass(count)"
            :title="`${row.sensor_name}, ${fullDate(days[index])}: ${count} ${count === 1 ? 'alerta' : 'alertas'}`"
          >
            {{ count || '' }}
          </td>
          <td class="text-center font-bold tabular-nums text-slate-700">{{ total(row) }}</td>
        </tr>
      </tbody>
    </table>

    <p class="mt-2 flex flex-wrap items-center gap-3 text-xs text-slate-500">
      <span class="flex items-center gap-1"><span class="h-3 w-3 rounded-sm bg-slate-100" aria-hidden="true"></span>Sin alertas</span>
      <span class="flex items-center gap-1"><span class="h-3 w-3 rounded-sm bg-warning-light" aria-hidden="true"></span>1</span>
      <span class="flex items-center gap-1"><span class="h-3 w-3 rounded-sm bg-warning" aria-hidden="true"></span>2–3</span>
      <span class="flex items-center gap-1"><span class="h-3 w-3 rounded-sm bg-danger" aria-hidden="true"></span>4 o más</span>
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import EmptyState from './EmptyState.vue'
import { floorLabel } from '../utils/floors'

const props = defineProps({
  // The 7 days of the week as 'YYYY-MM-DD' (UTC), Monday first
  days: { type: Array, default: () => [] },
  // WeeklyAlertsRow[]: { sensor_id, sensor_name, floor, counts }
  rows: { type: Array, default: () => [] },
  // Highlights the sensor shown in the detail panel
  selectedId: { type: String, default: null },
  // Name of the building, for screen readers
  siteName: { type: String, default: '' },
})

defineEmits(['select'])

// The days are UTC dates: format them in UTC so Monday stays Monday
const weekday = new Intl.DateTimeFormat('es-ES', { weekday: 'short', timeZone: 'UTC' })
const dayFormat = new Intl.DateTimeFormat('es-ES', { day: 'numeric', timeZone: 'UTC' })
const longFormat = new Intl.DateTimeFormat('es-ES', { weekday: 'long', day: 'numeric', month: 'long', timeZone: 'UTC' })

function toDate(day) {
  return new Date(`${day}T00:00:00Z`)
}

function weekdayLabel(day) {
  const name = weekday.format(toDate(day)).replace('.', '')
  return name.charAt(0).toUpperCase() + name.slice(1)
}

function dayNumber(day) {
  return dayFormat.format(toDate(day))
}

function fullDate(day) {
  return day ? longFormat.format(toDate(day)) : ''
}

const todayIndex = computed(() => props.days.indexOf(new Date().toISOString().slice(0, 10)))

const caption = computed(() =>
  `Alertas de la semana por sensor y día${props.siteName ? ` en ${props.siteName}` : ''}`,
)

function total(row) {
  return row.counts.reduce((sum, count) => sum + count, 0)
}

// Top floor first, as in BuildingStack, then by name
const sortedRows = computed(() =>
  [...props.rows].sort(
    (a, b) => (b.floor ?? 0) - (a.floor ?? 0) || a.sensor_name.localeCompare(b.sensor_name, 'es'),
  ),
)

// Full class names so Tailwind generates them
function cellClass(count) {
  if (!count) return 'bg-slate-100 text-slate-400'
  if (count === 1) return 'bg-warning-light text-warning-dark'
  if (count <= 3) return 'bg-warning text-white'
  return 'bg-danger text-white'
}
</script>
