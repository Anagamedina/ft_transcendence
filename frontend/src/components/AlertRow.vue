<!--
  ALERT ROW
  One row of an alerts table (<tr>): message, client, sensor, severity, state,
  date and the acknowledge / resolve buttons. Presentational: it receives the
  alert by props and emits the chosen action; the parent calls the store.
  Same columns as the admin alerts table (#153), so it can replace that row.
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
      <span class="block text-xs text-slate-400">{{ alert.type }}</span>
    </td>
    <td class="px-4 py-3 text-slate-600">
      {{ alert.organization_name || '—' }}
    </td>
    <td class="px-4 py-3 text-slate-600">
      {{ alert.sensor_name || '—' }}
      <span class="block text-xs text-slate-400">{{ alert.site_name }}</span>
    </td>
    <td class="whitespace-nowrap px-4 py-3">
      <span class="rounded-full px-2.5 py-1 text-xs font-medium" :class="severityClass">
        {{ severityLabel }}
      </span>
    </td>
    <td class="whitespace-nowrap px-4 py-3 text-slate-600">
      {{ stateLabel }}
    </td>
    <td class="whitespace-nowrap px-4 py-3 text-slate-600">
      {{ formatDate(alert.created_at) }}
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

const props = defineProps({
  // AlertResponse: message, type, organization_name, sensor_name, site_name,
  // severity, status (ACTIVE | RESOLVED), state (ACTIVE | ACKNOWLEDGED | RESOLVED), created_at
  alert: { type: Object, required: true },
  // True while an action on this alert is running: disables its buttons
  busy: { type: Boolean, default: false },
})

// Both events send the alert id
defineEmits(['acknowledge', 'resolve'])

const STATE_LABELS = {
  ACTIVE: 'Sin reconocer',
  ACKNOWLEDGED: 'Reconocida',
  RESOLVED: 'Resuelta',
}

const SEVERITY_LABELS = {
  CRITICAL: 'Crítica',
  WARNING: 'Advertencia',
}

const SEVERITY_CLASSES = {
  CRITICAL: 'bg-red-100 text-red-800',
  WARNING: 'bg-amber-100 text-amber-800',
}

// Unknown values are shown as they come, so a new enum value never breaks the row
const stateLabel = computed(() => STATE_LABELS[props.alert.state] || props.alert.state || '—')
const severityLabel = computed(
  () => SEVERITY_LABELS[props.alert.severity] || props.alert.severity || '—'
)
const severityClass = computed(
  () => SEVERITY_CLASSES[props.alert.severity] || 'bg-slate-100 text-slate-700'
)

// Short Spanish date and time, e.g. "8/9/26, 10:20"
const dateFormat = new Intl.DateTimeFormat('es-ES', { dateStyle: 'short', timeStyle: 'short' })

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '—' : dateFormat.format(date)
}
</script>