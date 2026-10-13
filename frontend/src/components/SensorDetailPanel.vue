<!--
  SENSOR DETAIL PANEL
  Detail of the selected sensor next to the building (F5), as in the
  C-Edificio mockup: name, floor, health pill, four key figures (current
  value, allowed range, last reading, alerts in 7 days) and the pressure chart.
  Pure visual component: the parent passes the sensor, its readings and the
  alert count, and decides what "loading", "error" and "retry" mean.
  Shape: sensor = SensorResponse (B3), readings = ReadingResponse[] (B7).
  Usage:
    <SensorDetailPanel
      :sensor="selectedSensor" :readings="readings" :alert-count="3"
      :loading="loadingReadings" :error="readingsError" @retry="loadReadings" />
-->

<template>
  <section
    v-if="sensor"
    class="flex flex-col gap-3.5 rounded-xl border border-slate-200 bg-white p-5"
    :aria-label="`Detalle del sensor ${sensor.name}`"
  >
    <header class="flex items-center justify-between gap-3">
      <div class="flex min-w-0 flex-col gap-0.5">
        <h2 class="break-words text-lg font-bold text-aqua-900">{{ sensor.name }}</h2>
        <span class="text-[13px] text-slate-600">{{ floorLabel(sensor.floor ?? 0) }}</span>
      </div>
      <StatusPill type="SensorHealth" :value="sensor.health" class="shrink-0" />
    </header>

    <dl class="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
      <div v-for="item in figures" :key="item.label" class="flex flex-col gap-0.5 rounded-lg bg-slate-50 px-3 py-2.5">
        <dt class="text-xs text-slate-600">{{ item.label }}</dt>
        <dd class="text-[17px] font-bold tabular-nums text-aqua-900">{{ item.value }}</dd>
      </div>
    </dl>

    <figure class="m-0 flex flex-col gap-1.5">
      <figcaption class="text-[13px] font-semibold text-slate-700">
        Presión de los últimos {{ days }} días ({{ unit }})
      </figcaption>
      <LoadingState v-if="loading" message="Cargando lecturas…" compact />
      <ErrorState v-else-if="error" :message="error" compact @retry="$emit('retry')" />
      <PressureChart
        v-else
        :readings="readings"
        :min-pressure="sensor.min_pressure"
        :max-pressure="sensor.max_pressure"
        :unit="unit"
      />
    </figure>

    <p class="text-xs text-slate-500">
      La franja verde es el rango permitido del sensor. Toca otro sensor del edificio para ver su gráfica.
    </p>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import StatusPill from './StatusPill.vue'
import PressureChart from './PressureChart.vue'
import LoadingState from './LoadingState.vue'
import ErrorState from './ErrorState.vue'
import { floorLabel } from '../utils/floors'

const props = defineProps({
  // SensorResponse (B3); null hides the panel
  sensor: { type: Object, default: null },
  // ReadingResponse[] of the period shown in the chart
  readings: { type: Array, default: () => [] },
  // Alerts of this sensor in the period; null shows '—' until the data exists
  alertCount: { type: Number, default: null },
  loading: { type: Boolean, default: false },
  // Error message from the parent; shows ErrorState with a retry button
  error: { type: String, default: '' },
  // Period of the chart, only used in the caption
  days: { type: Number, default: 7 },
})

defineEmits(['retry'])

const unit = computed(() => props.sensor?.unit || 'bar')

// Spanish number format, as in the mockup: '1,3' and '2,0–6,0'
const oneDecimal = new Intl.NumberFormat('es-ES', { minimumFractionDigits: 1, maximumFractionDigits: 1 })

function formatValue(value) {
  return value === null || value === undefined ? '—' : `${oneDecimal.format(value)} ${unit.value}`
}

// 'hace 1 min', 'hace 3 h', 'hace 2 días'
const relative = new Intl.RelativeTimeFormat('es-ES', { numeric: 'always', style: 'short' })

function timeAgo(isoDate) {
  if (!isoDate) return 'Nunca'
  const seconds = Math.round((new Date(isoDate).getTime() - Date.now()) / 1000)
  if (Number.isNaN(seconds)) return '—'
  if (seconds > -60) return 'Ahora'
  if (seconds > -3600) return relative.format(Math.round(seconds / 60), 'minute')
  if (seconds > -86400) return relative.format(Math.round(seconds / 3600), 'hour')
  return relative.format(Math.round(seconds / 86400), 'day')
}

const figures = computed(() => {
  const s = props.sensor
  if (!s) return []
  return [
    { label: 'Valor actual', value: formatValue(s.last_value) },
    {
      label: 'Rango permitido',
      value: `${oneDecimal.format(s.min_pressure)}–${oneDecimal.format(s.max_pressure)} ${unit.value}`,
    },
    { label: 'Última lectura', value: timeAgo(s.last_seen_at) },
    { label: `Alertas (${props.days} días)`, value: props.alertCount ?? '—' },
  ]
})
</script>
