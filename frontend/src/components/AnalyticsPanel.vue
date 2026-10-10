<!--
  ANALYTICS PANEL (F19)
  Date range + CSV export + period KPIs + three interactive charts:
  alerts per day (line), alerts per client or sensor (bar) and alerts by
  severity (pie). Data comes from the analytics store (one request to
  GET /api/analytics/export?format=json, scoped to the user's organization).
  Refreshes itself every 30 s while the tab is visible.
-->

<script setup>
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useAnalyticsStore } from '../stores/analytics'
import { useAutoRefresh } from '../composables/useAutoRefresh'
import AnalyticsChart from './AnalyticsChart.vue'
import KPICard from './KPICard.vue'
import AppIcon from './AppIcon.vue'
import LoadingState from './LoadingState.vue'
import EmptyState from './EmptyState.vue'
import ErrorState from './ErrorState.vue'

const REFRESH_MS = 30000
const PRESETS = [7, 30, 90]

// Validated palette (light surface): blue = all alerts, red = critical,
// amber = warning. Severity keeps the same color in every chart.
const COLOR_TOTAL = '#2a78d6'
const COLOR_CRITICAL = '#e34948'
const COLOR_WARNING = '#eda100'

const store = useAnalyticsStore()
const { fromDate, toDate, status, error, rangeError, lastUpdated, exporting } = storeToRefs(store)

onMounted(() => store.fetchRows())
useAutoRefresh(() => store.fetchRows({ background: true }), REFRESH_MS)

// Date inputs: reload only when the range is valid.
function onRangeInput() {
  if (!rangeError.value) store.fetchRows()
}

const dayFormat = new Intl.DateTimeFormat('es-ES', { day: 'numeric', month: 'short', timeZone: 'UTC' })
const formatDay = (iso) => dayFormat.format(new Date(`${iso}T00:00:00Z`))

const lineData = computed(() => ({
  labels: store.alertsByDay.labels.map(formatDay),
  datasets: [
    { label: 'Total', data: store.alertsByDay.total, color: COLOR_TOTAL },
    { label: 'Críticas', data: store.alertsByDay.critical, color: COLOR_CRITICAL },
  ],
}))

// A client only has one organization: default to one bar per sensor.
const organizations = computed(() => new Set(store.rows.map((r) => r.organization)).size)
const barChoice = ref(null)
const barBy = computed(() => barChoice.value ?? (organizations.value > 1 ? 'organization' : 'sensor_name'))
const barData = computed(() => {
  const { labels, values } = store.alertsBy(barBy.value)
  return {
    labels,
    datasets: [{ label: 'Alertas', data: values, color: COLOR_TOTAL }],
  }
})

const pieData = computed(() => ({
  labels: store.alertsBySeverity.labels,
  datasets: [{ label: 'Alertas', data: store.alertsBySeverity.values, color: [COLOR_WARNING, COLOR_CRITICAL] }],
}))

const isEmpty = computed(() => store.totalAlerts === 0 && store.totalReadings === 0)
const updatedAt = computed(() =>
  lastUpdated.value ? lastUpdated.value.toLocaleTimeString('es-ES') : null
)
</script>

<template>
  <section class="bg-white border border-gray-200 rounded-xl shadow-md p-5 mb-8" aria-labelledby="analytics-title">
    <!-- Filters: one row above the charts -->
    <header class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4 mb-5">
      <div>
        <h2 id="analytics-title" class="text-lg font-bold text-gray-800">Analítica</h2>
        <p class="text-sm text-gray-500" aria-live="polite">
          <template v-if="updatedAt">Actualizado a las {{ updatedAt }} · se refresca cada 30 s</template>
          <template v-else>Alertas y lecturas del periodo elegido</template>
        </p>
      </div>

      <div class="flex flex-wrap items-end gap-3">
        <div class="flex gap-1" role="group" aria-label="Periodos rápidos">
          <button
            v-for="n in PRESETS"
            :key="n"
            type="button"
            class="px-3 py-2 text-sm rounded-lg border border-gray-300 text-gray-700 hover:bg-aqua-50"
            @click="store.setLastDays(n)"
          >
            {{ n }} días
          </button>
        </div>
        <label class="flex flex-col text-xs font-semibold text-gray-600">
          Desde
          <input v-model="fromDate" type="date" class="mt-1 border border-gray-300 rounded-lg px-2 py-1.5 text-sm" @change="onRangeInput" />
        </label>
        <label class="flex flex-col text-xs font-semibold text-gray-600">
          Hasta
          <input v-model="toDate" type="date" class="mt-1 border border-gray-300 rounded-lg px-2 py-1.5 text-sm" @change="onRangeInput" />
        </label>
        <button
          type="button"
          class="bg-aqua-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-aqua-800 transition disabled:opacity-50"
          :disabled="!!rangeError || exporting"
          @click="store.exportCsv()"
        >
          {{ exporting ? 'Exportando…' : 'Exportar CSV' }}
        </button>
      </div>
    </header>

    <p v-if="rangeError" class="mb-4 text-sm font-semibold text-danger" role="alert">{{ rangeError }}</p>

    <LoadingState v-if="status === 'loading' || status === 'idle'" message="Cargando analítica…" />
    <ErrorState
      v-else-if="status === 'error'"
      :message="error?.message"
      @retry="store.fetchRows()"
    />
    <EmptyState
      v-else-if="isEmpty"
      title="Sin datos en este periodo"
      message="No hay alertas ni lecturas entre esas fechas. Prueba con un periodo más largo."
      icon="bar-chart"
    />

    <template v-else>
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <KPICard label="Alertas en el periodo" :value="store.totalAlerts">
          <template #icon><AppIcon name="alert" /></template>
        </KPICard>
        <KPICard label="Alertas críticas" :value="store.criticalAlerts">
          <template #icon><AppIcon name="alert" /></template>
        </KPICard>
        <KPICard label="Resueltas" :value="store.resolvedPercent === null ? '—' : `${store.resolvedPercent} %`">
          <template #icon><AppIcon name="bar-chart" /></template>
        </KPICard>
        <KPICard label="Lecturas recibidas" :value="store.totalReadings.toLocaleString('es-ES')">
          <template #icon><AppIcon name="droplet" /></template>
        </KPICard>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <figure class="lg:col-span-2">
          <figcaption class="text-sm font-semibold text-gray-700 mb-2">Alertas por día</figcaption>
          <AnalyticsChart type="line" aria-label="Alertas por día, total y críticas" v-bind="lineData" />
        </figure>

        <figure>
          <figcaption class="text-sm font-semibold text-gray-700 mb-2">Alertas por gravedad</figcaption>
          <AnalyticsChart type="pie" aria-label="Alertas por gravedad" v-bind="pieData" />
        </figure>

        <figure class="lg:col-span-3">
          <div class="flex items-center justify-between mb-2">
            <figcaption class="text-sm font-semibold text-gray-700">
              Alertas por {{ barBy === 'organization' ? 'cliente' : 'sensor' }}
            </figcaption>
            <div class="flex gap-1" role="group" aria-label="Agrupar alertas por">
              <button
                v-for="opt in [{ key: 'organization', text: 'Cliente' }, { key: 'sensor_name', text: 'Sensor' }]"
                :key="opt.key"
                type="button"
                class="px-3 py-1 text-xs rounded-lg border"
                :class="barBy === opt.key ? 'bg-aqua-600 text-white border-aqua-600' : 'border-gray-300 text-gray-700'"
                :aria-pressed="barBy === opt.key"
                @click="barChoice = opt.key"
              >
                {{ opt.text }}
              </button>
            </div>
          </div>
          <EmptyState v-if="!barData.labels.length" title="Sin alertas en este periodo" icon="alert" compact />
          <AnalyticsChart
            v-else
            type="bar"
            horizontal
            :aria-label="`Alertas por ${barBy === 'organization' ? 'cliente' : 'sensor'}`"
            v-bind="barData"
          />
        </figure>
      </div>
    </template>
  </section>
</template>
