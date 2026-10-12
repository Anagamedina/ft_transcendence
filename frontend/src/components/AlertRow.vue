<!--
  ALERT ROW
  One row of an alerts table (<tr>): message, client, sensor, severity, state
  (with when it was acknowledged or resolved), date (with how long it has been
  open or how long it lasted) and the acknowledge / resolve buttons.
  Presentational: it receives the alert by props and emits the chosen action;
  the parent calls the store.
  Usage (inside <tbody>):
    <AlertRow
      v-for="alert in alerts" :key="alert.id"
      :alert="alert"
      :busy="busyAlertId === alert.id"
      @acknowledge="acknowledge"
      @resolve="resolve"
    />
-->

<template>
  <tr>
    <td class="min-w-48 px-4 py-3 text-slate-800">
      {{ alert.message || '—' }}
      <span class="block text-xs text-slate-400">{{ label('AlertType', alert.type) }}</span>
    </td>
    <td class="px-4 py-3 text-slate-600">
      {{ alert.organization_name || '—' }}
    </td>
    <td class="px-4 py-3 text-slate-600">
      {{ alert.sensor_name || '—' }}
      <span class="block text-xs text-slate-400">{{ alert.site_name }}</span>
    </td>
    <td class="px-4 py-3">
      <StatusPill type="AlertSeverity" :value="alert.severity" />
    </td>
    <td class="px-4 py-3">
      <StatusPill type="AlertState" :value="alert.state" />
      <span v-if="actionDate" class="mt-1 block whitespace-nowrap text-xs text-slate-400">
        {{ actionDate }}
      </span>
    </td>
    <td class="whitespace-nowrap px-4 py-3 text-slate-600">
      {{ formatDate(alert.created_at) }}
      <span v-if="durationText" class="block text-xs text-slate-400">{{ durationText }}</span>
    </td>
    <td class="whitespace-nowrap px-4 py-3">
      <div class="flex flex-wrap gap-2">
        <!-- Acknowledge: only while nobody has seen it yet (state ACTIVE) -->
        <button
          v-if="alert.state === 'ACTIVE'"
          type="button"
          class="rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-medium hover:bg-slate-50 disabled:opacity-50"
          :disabled="busy"
          @click="$emit('acknowledge', alert.id)"
        >
          Reconocer
        </button>
        <!-- Resolve: while the stored status is ACTIVE, acknowledged or not -->
        <button
          v-if="alert.status === 'ACTIVE'"
          type="button"
          class="rounded-md bg-aqua-900 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-aqua-800 disabled:opacity-50"
          :disabled="busy"
          @click="$emit('resolve', alert.id)"
        >
          Resolver
        </button>
        <span v-if="alert.status === 'RESOLVED'" class="text-xs text-slate-500">
          Sin acciones
        </span>
      </div>
    </td>
  </tr>
</template>

<script setup>
import { computed } from 'vue'
import StatusPill from './StatusPill.vue'
import { useLabels } from '../composables/useLabels'

const props = defineProps({
  // AlertResponse: message, type, organization_name, sensor_name, site_name,
  // severity, status (ACTIVE | RESOLVED), state (ACTIVE | ACKNOWLEDGED | RESOLVED),
  // created_at, acknowledged_at, resolved_at
  alert: { type: Object, required: true },
  // True while an action on this alert is running: disables its buttons
  busy: { type: Boolean, default: false },
})

// Both events send the alert id
defineEmits(['acknowledge', 'resolve'])

const { label } = useLabels()

// Short Spanish date and time, e.g. "8/9/26, 10:20"
const dateFormat = new Intl.DateTimeFormat('es-ES', { dateStyle: 'short', timeStyle: 'short' })

function toDate(value) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function formatDate(value) {
  const date = toDate(value)
  return date ? dateFormat.format(date) : '—'
}

// Human duration: "menos de 1 min", "25 min", "3 h 10 min", "2 d 4 h"
function formatDuration(ms) {
  const minutes = Math.floor(ms / 60000)
  if (minutes < 1) return 'menos de 1 min'
  if (minutes < 60) return `${minutes} min`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return minutes % 60 ? `${hours} h ${minutes % 60} min` : `${hours} h`
  const days = Math.floor(hours / 24)
  return hours % 24 ? `${days} d ${hours % 24} h` : `${days} d`
}

// When the last action happened: shown under the state pill
const actionDate = computed(() => {
  const { state, acknowledged_at: acknowledgedAt, resolved_at: resolvedAt } = props.alert
  if (state === 'RESOLVED' && toDate(resolvedAt)) return `el ${formatDate(resolvedAt)}`
  if (state === 'ACKNOWLEDGED' && toDate(acknowledgedAt)) return `el ${formatDate(acknowledgedAt)}`
  return ''
})

// How long it has been open (still active) or how long it lasted (resolved)
const durationText = computed(() => {
  const start = toDate(props.alert.created_at)
  if (!start) return ''
  const resolved = toDate(props.alert.resolved_at)
  const end = resolved || new Date()
  if (end < start) return ''
  const text = formatDuration(end - start)
  return resolved ? `Duró ${text}` : `Abierta ${text}`
})
</script>