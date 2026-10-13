<!--
  PRESSURE CHART
  Line chart of a sensor's pressure (F5), usually the last 7 days, as in the
  C-Edificio mockup: the allowed range (min_pressure to max_pressure) is a
  green band with dashed edges, so readings outside it stand out at a glance.
  Pure component: it receives the readings, it never fetches.
  Accessibility: the canvas has an aria-label, and a visually hidden summary
  gives the key figures to screen readers.
  Usage:
    <PressureChart :readings="readings" :min-pressure="2" :max-pressure="6" unit="bar" />
-->

<template>
  <EmptyState
    v-if="!points.length"
    icon="bar-chart"
    title="Sin lecturas en este periodo"
    message="Cuando el sensor envíe datos, verás aquí su presión."
    compact
  />

  <div v-else class="relative w-full" :style="{ height }">
    <canvas ref="canvas" role="img" :aria-label="ariaLabel"></canvas>
    <p class="sr-only">{{ summary }}</p>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Filler,
} from 'chart.js'
import EmptyState from './EmptyState.vue'

// Only what this chart needs (registering twice is harmless).
// Filler paints the green band between the two threshold lines.
Chart.register(LineController, LineElement, PointElement, CategoryScale, LinearScale, Tooltip, Filler)

const props = defineProps({
  // ReadingResponse[]: { pressure, measured_at }
  readings: { type: Array, default: () => [] },
  minPressure: { type: Number, default: null },
  maxPressure: { type: Number, default: null },
  unit: { type: String, default: 'bar' },
  height: { type: String, default: '240px' },
})

// Colours from the mockup (Chart.js needs plain values, not Tailwind classes)
const LINE = '#0369a1' // aqua-600
const BAND = '#ecfdf5' // green band: allowed range
const BAND_EDGE = '#10b981' // success
const INK = '#64748b' // slate-500
const GRID = '#e2e8f0' // slate-200

const tooltipDate = new Intl.DateTimeFormat('es-ES', {
  weekday: 'short',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})
const weekday = new Intl.DateTimeFormat('es-ES', { weekday: 'short' })
const number = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 2 })

// Readings sorted by time, oldest first
const points = computed(() =>
  [...props.readings]
    .filter((r) => r && r.pressure !== null && r.pressure !== undefined && r.measured_at)
    .sort((a, b) => new Date(a.measured_at) - new Date(b.measured_at)),
)

const hasRange = computed(() => props.minPressure !== null && props.maxPressure !== null)

function isOutOfRange(value) {
  if (props.minPressure !== null && value < props.minPressure) return true
  if (props.maxPressure !== null && value > props.maxPressure) return true
  return false
}

const ariaLabel = computed(() => `Gráfica de presión en ${props.unit}, ${points.value.length} lecturas`)

const summary = computed(() => {
  if (!points.value.length) return ''
  const values = points.value.map((p) => p.pressure)
  const outside = values.filter(isOutOfRange).length
  return (
    `Última lectura ${number.format(values[values.length - 1])} ${props.unit}. ` +
    `Mínimo ${number.format(Math.min(...values))} y máximo ${number.format(Math.max(...values))} ${props.unit}. ` +
    `Rango permitido de ${props.minPressure ?? '—'} a ${props.maxPressure ?? '—'} ${props.unit}. ` +
    `${outside} lecturas fuera de rango.`
  )
})

// Day name ('Sáb') once per day, on the first reading from midday on, so each
// name sits in the middle of its day and two names never overlap
function dayTick(index) {
  const current = new Date(points.value[index]?.measured_at)
  if (current.getHours() < 12) return null
  const previous = index > 0 ? new Date(points.value[index - 1].measured_at) : null
  if (previous && previous.toDateString() === current.toDateString() && previous.getHours() >= 12) return null
  const name = weekday.format(current).replace('.', '')
  return name.charAt(0).toUpperCase() + name.slice(1)
}

const canvas = ref(null)
let chart = null

function chartData() {
  const labels = points.value.map((p) => tooltipDate.format(new Date(p.measured_at)))
  const values = points.value.map((p) => p.pressure)
  const last = values.length - 1
  const datasets = [
    {
      label: 'Presión',
      data: values,
      borderColor: LINE,
      backgroundColor: LINE,
      borderWidth: 2,
      // Only the latest reading gets a visible point
      pointRadius: values.map((_, i) => (i === last ? 4 : 0)),
      pointHoverRadius: 5,
      pointHitRadius: 10,
      tension: 0,
      order: 0, // drawn on top of the band
    },
  ]
  if (hasRange.value) {
    datasets.push(
      band('Mínimo', props.minPressure, labels.length, false),
      // fill '-1' paints from this line down to the previous dataset (the minimum)
      band('Máximo', props.maxPressure, labels.length, '-1'),
    )
  }
  return { labels, datasets }
}

function band(name, value, length, fill) {
  return {
    label: name,
    data: Array(length).fill(value),
    borderColor: BAND_EDGE,
    backgroundColor: BAND,
    borderWidth: 1,
    borderDash: [4, 4],
    pointRadius: 0,
    pointHitRadius: 0,
    fill,
    order: 1,
  }
}

function chartOptions() {
  const values = points.value.map((p) => p.pressure)
  const high = Math.max(...values, props.maxPressure ?? 0)
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        // Only the pressure in the tooltip; the range is explained under the chart
        filter: (item) => item.datasetIndex === 0,
        callbacks: { label: (ctx) => `Presión: ${number.format(ctx.parsed.y)} ${props.unit}` },
      },
    },
    scales: {
      x: {
        ticks: {
          color: INK,
          font: { size: 11 },
          maxRotation: 0,
          autoSkip: false,
          callback: (_, index) => dayTick(index),
        },
        grid: { display: false },
        border: { display: false },
      },
      y: {
        beginAtZero: true,
        suggestedMax: Math.ceil((high + 1) / 2) * 2,
        ticks: { color: INK, font: { size: 11 }, stepSize: 2 },
        grid: { color: GRID },
        border: { display: false },
      },
    },
  }
}

// The canvas only exists when there are readings (v-else), so the chart is
// created or destroyed whenever that changes.
async function render() {
  await nextTick()
  if (!canvas.value || !points.value.length) {
    chart?.destroy()
    chart = null
    return
  }
  if (chart && chart.canvas !== canvas.value) {
    chart.destroy()
    chart = null
  }
  if (!chart) {
    chart = new Chart(canvas.value, { type: 'line', data: chartData(), options: chartOptions() })
    return
  }
  chart.data = chartData()
  chart.options = chartOptions()
  chart.update('none')
}

onMounted(render)
watch(() => [props.readings, props.minPressure, props.maxPressure, props.unit], render, { deep: true })

onBeforeUnmount(() => {
  chart?.destroy()
  chart = null
})
</script>
