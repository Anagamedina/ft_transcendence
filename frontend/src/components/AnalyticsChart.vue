<!--
  ANALYTICS CHART
  Thin wrapper around Chart.js for the analytics panel (F19): line, bar or pie.
  The parent passes plain labels + datasets; this component owns the Chart
  instance (created on mount, updated when the data changes, destroyed on
  unmount so no canvas leaks between pages).
  Accessibility: the canvas has an aria-label, and a visually hidden table
  repeats the data for screen readers.
-->

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import {
  Chart,
  LineController,
  BarController,
  PieController,
  LineElement,
  PointElement,
  BarElement,
  ArcElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from 'chart.js'

// Only what the three chart types need (keeps the bundle small).
Chart.register(
  LineController,
  BarController,
  PieController,
  LineElement,
  PointElement,
  BarElement,
  ArcElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
)

const props = defineProps({
  type: { type: String, required: true, validator: (t) => ['line', 'bar', 'pie'].includes(t) },
  // Short description read by screen readers instead of the canvas
  ariaLabel: { type: String, required: true },
  labels: { type: Array, required: true },
  // [{ label, data: [numbers], color }]
  datasets: { type: Array, required: true },
  // bar only: horizontal bars read better with long names (clients, sensors)
  horizontal: { type: Boolean, default: false },
  height: { type: String, default: '260px' },
})

// Recessive axes and grid; text in ink colors, never the series color.
const INK = '#4b5563'
const GRID = '#e5e7eb'
const SURFACE = '#ffffff'

const canvas = ref(null)
let chart = null

function chartData() {
  return {
    labels: props.labels,
    datasets: props.datasets.map((ds) => {
      if (props.type === 'pie') {
        return {
          label: ds.label,
          data: ds.data,
          backgroundColor: ds.color,
          borderColor: SURFACE,
          borderWidth: 2, // 2px surface gap between slices
          hoverOffset: 6,
        }
      }
      if (props.type === 'bar') {
        return {
          label: ds.label,
          data: ds.data,
          backgroundColor: ds.color,
          borderRadius: 4,
          borderSkipped: 'start', // rounded only at the data end
          maxBarThickness: 28,
        }
      }
      return {
        label: ds.label,
        data: ds.data,
        borderColor: ds.color,
        backgroundColor: ds.color,
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHitRadius: 12, // hit target bigger than the mark
        cubicInterpolationMode: 'monotone', // smooth, but never dips below 0 or overshoots a count
      }
    }),
  }
}

function chartOptions() {
  const legend = {
    display: props.datasets.length > 1 || props.type === 'pie',
    position: 'bottom',
    labels: { color: INK, usePointStyle: true, boxWidth: 8 },
  }
  if (props.type === 'pie') {
    // Values in the legend text: identity never depends on color alone.
    legend.labels.generateLabels = (c) =>
      Chart.overrides.pie.plugins.legend.labels
        .generateLabels(c)
        .map((item) => ({ ...item, text: `${item.text} · ${c.data.datasets[0].data[item.index]}` }))
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend },
    }
  }
  const valueAxis = {
    beginAtZero: true,
    ticks: { color: INK, precision: 0 },
    grid: { color: GRID },
    border: { display: false },
  }
  const categoryAxis = {
    ticks: { color: INK, maxRotation: 0, autoSkip: true, maxTicksLimit: 8 },
    grid: { display: false },
  }
  return {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: props.horizontal ? 'y' : 'x',
    // Line: tooltip for every series at the hovered day (crosshair-like).
    interaction: props.type === 'line' ? { mode: 'index', intersect: false } : { mode: 'nearest', intersect: true },
    plugins: { legend },
    scales: props.horizontal
      ? { x: valueAxis, y: categoryAxis }
      : { x: categoryAxis, y: valueAxis },
  }
}

onMounted(() => {
  chart = new Chart(canvas.value, { type: props.type, data: chartData(), options: chartOptions() })
})

// New data (range change or periodic refresh): update in place, no flicker.
watch(
  () => [props.labels, props.datasets],
  () => {
    if (!chart) return
    chart.data = chartData()
    chart.options = chartOptions()
    chart.update('none')
  },
  { deep: true }
)

onBeforeUnmount(() => {
  chart?.destroy()
  chart = null
})
</script>

<template>
  <div class="relative w-full" :style="{ height }">
    <canvas ref="canvas" role="img" :aria-label="ariaLabel"></canvas>
    <table class="sr-only">
      <caption>{{ ariaLabel }}</caption>
      <thead>
        <tr>
          <th scope="col"></th>
          <th v-for="ds in datasets" :key="ds.label" scope="col">{{ ds.label }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(label, i) in labels" :key="label">
          <th scope="row">{{ label }}</th>
          <td v-for="ds in datasets" :key="ds.label">{{ ds.data[i] }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
