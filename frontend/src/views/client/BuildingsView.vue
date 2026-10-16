<!--
  CLIENT BUILDINGS VIEW (F8)
  Client home page, replaces the old client DashboardView:
    - KPIs of the organization (B9 overview, loaded by ClientLayout).
    - One card per building (B2). With a single building it opens directly.
    - The open building floor by floor (BuildingStack, F4) and the selected
      sensor with its 7-day pressure chart (SensorDetailPanel + PressureChart,
      F5, series from B7).
    - Alerts of the week by sensor and day (WeekAlertsGrid, B9).
  The open building lives in the URL (/app?site=<id>), so reloading and the
  back button keep it. Data reloads every minute and when the tab is visible
  again (useAutoRefresh). The trial banner is in ClientLayout (TrialBanner).
  Detailed alerts are in /app/alerts (F9-C).
-->

<template>
  <div class="mx-auto max-w-7xl space-y-6">
    <header class="flex flex-wrap items-end justify-between gap-3">
      <div class="min-w-0">
        <h1 class="text-2xl font-bold text-slate-900">
          {{ site ? site.name : 'Mis edificios' }}
        </h1>
        <p class="mt-1 text-sm text-slate-600">
          {{ site ? siteSummary : 'Estado de tus edificios, sensores y alertas.' }}
        </p>
      </div>
      <button
        v-if="site && sites.length > 1"
        type="button"
        class="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        @click="openSite(null)"
      >
        ← Todos los edificios
      </button>
    </header>

    <!-- KPIs -->
    <section aria-label="Indicadores" class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <KPICard v-for="kpi in kpis" :key="kpi.label" :label="kpi.label" :value="kpi.value">
        <template #icon><AppIcon :name="kpi.icon" /></template>
      </KPICard>
    </section>

    <LoadingState v-if="sitesLoading" message="Cargando tus edificios…" />
    <ErrorState v-else-if="sitesError" :message="sitesError" @retry="loadSites" />
    <EmptyState
      v-else-if="!sites.length"
      icon="building"
      title="Todavía no tienes edificios"
      message="Cuando AquaGuard dé de alta tu edificio, aparecerá aquí."
    />

    <!-- Building cards -->
    <section v-else-if="!site" aria-label="Edificios" class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
      <button
        v-for="item in sortedSites"
        :key="item.id"
        type="button"
        class="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:border-aqua-300 hover:shadow-md"
        @click="openSite(item.id)"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <h2 class="break-words text-lg font-bold text-aqua-900">{{ item.name }}</h2>
            <p class="text-sm text-slate-600">{{ item.address || label('BuildingType', item.building_type) }}</p>
          </div>
          <StatusPill type="SiteStatus" :value="item.status" class="shrink-0" />
        </div>
        <dl class="grid grid-cols-3 gap-2 text-sm">
          <div class="rounded-lg bg-slate-50 px-3 py-2">
            <dt class="text-xs text-slate-500">Sensores</dt>
            <dd class="font-bold tabular-nums text-slate-800">{{ item.sensor_count }}</dd>
          </div>
          <div class="rounded-lg bg-slate-50 px-3 py-2">
            <dt class="text-xs text-slate-500">Con aviso</dt>
            <dd class="font-bold tabular-nums text-slate-800">{{ alertingIn(item.id) }}</dd>
          </div>
          <div class="rounded-lg bg-slate-50 px-3 py-2">
            <dt class="text-xs text-slate-500">Plantas</dt>
            <dd class="font-bold tabular-nums text-slate-800">{{ floorsText(item) }}</dd>
          </div>
        </dl>
      </button>
    </section>

    <!-- Open building -->
    <template v-else>
      <LoadingState v-if="sensorsLoading" message="Cargando sensores…" />
      <ErrorState v-else-if="sensorsError" :message="sensorsError" @retry="loadSensors" />

      <div v-else class="grid items-start gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <BuildingStack
          :name="site.name"
          :floors="site.floors"
          :basements="site.basements"
          :sensors="siteSensors"
          :selected-id="selectedId"
          @select="selectSensor"
        />

        <div ref="sidePanel">
          <SensorDetailPanel
            v-if="selectedSensor"
            :sensor="selectedSensor"
            :readings="readings"
            :alert-count="alertCount"
            :loading="readingsLoading"
            :error="readingsError"
            @retry="loadReadings()"
          />
          <EmptyState
            v-else-if="siteSensors.length"
            icon="droplet"
            title="Elige un sensor"
            message="Toca un sensor del edificio para ver su gráfica de los últimos 7 días."
            compact
          />
        </div>
      </div>

      <section class="rounded-xl border border-slate-200 bg-white p-5" aria-labelledby="week-alerts-title">
        <div class="mb-3 flex flex-wrap items-baseline justify-between gap-2">
          <h2 id="week-alerts-title" class="text-lg font-bold text-slate-900">Alertas de la semana</h2>
          <RouterLink to="/app/alerts" class="text-sm font-medium text-aqua-700 hover:underline">
            Ver todas las alertas
          </RouterLink>
        </div>
        <LoadingState v-if="weeklyLoading" message="Cargando alertas de la semana…" compact />
        <ErrorState v-else-if="weeklyError" :message="weeklyError" compact @retry="loadWeekly()" />
        <WeekAlertsGrid
          v-else-if="weekly"
          :days="weekly.days"
          :rows="weekly.rows"
          :site-name="site.name"
          :selected-id="selectedId"
          @select="selectSensor"
        />
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import AppIcon from '../../components/AppIcon.vue'
import KPICard from '../../components/KPICard.vue'
import StatusPill from '../../components/StatusPill.vue'
import BuildingStack from '../../components/BuildingStack.vue'
import SensorDetailPanel from '../../components/SensorDetailPanel.vue'
import WeekAlertsGrid from '../../components/WeekAlertsGrid.vue'
import LoadingState from '../../components/LoadingState.vue'
import ErrorState from '../../components/ErrorState.vue'
import EmptyState from '../../components/EmptyState.vue'

import { useSitesStore } from '../../stores/sites.js'
import { useSensorsStore } from '../../stores/sensors.js'
import { useAlertsStore } from '../../stores/alerts.js'
import { useOverviewStore } from '../../stores/overview.js'
import readingService from '../../services/reading.service.js'
import analyticsService from '../../services/analytics.service.js'
import { useAutoRefresh } from '../../composables/useAutoRefresh'
import { useLabels } from '../../composables/useLabels'

const REFRESH_MS = 60 * 1000
const DAY_MS = 24 * 60 * 60 * 1000

const route = useRoute()
const router = useRouter()
const sitesStore = useSitesStore()
const sensorsStore = useSensorsStore()
const alertsStore = useAlertsStore()
const overviewStore = useOverviewStore()
const { label } = useLabels()

// ---------------------------------------------------------------------------
// KPIs. ClientLayout already loads and refreshes the overview (B9).
// ---------------------------------------------------------------------------
const kpis = computed(() => {
  const o = overviewStore.overview
  return [
    { label: 'Edificios', icon: 'building', value: o?.sites_total ?? '—' },
    { label: 'Sensores conectados', icon: 'wifi', value: o ? `${o.sensors_online} / ${o.sensors_total}` : '—' },
    { label: 'Alertas abiertas', icon: 'alert', value: o?.open_alerts ?? '—' },
    { label: 'Alertas críticas', icon: 'alert', value: o?.critical_open_alerts ?? '—' },
  ]
})

// ---------------------------------------------------------------------------
// Buildings and sensors. A refresh keeps the data on screen: "loading" only
// shows the spinner the first time.
// ---------------------------------------------------------------------------
const sites = computed(() => sitesStore.sites)
const sitesLoading = computed(() => ['idle', 'loading'].includes(sitesStore.status) && !sites.value.length)
const sitesError = computed(() =>
  sitesStore.status === 'error' ? sitesStore.error?.message || 'No se han podido cargar tus edificios.' : '',
)
const sensorsLoading = computed(
  () => ['idle', 'loading'].includes(sensorsStore.status) && !sensorsStore.sensors.length,
)
const sensorsError = computed(() =>
  sensorsStore.status === 'error' ? sensorsStore.error?.message || 'No se han podido cargar los sensores.' : '',
)

async function loadSites() {
  try {
    await sitesStore.fetchSites()
  } catch {
    // The store exposes the error state to the view
  }
}

async function loadSensors() {
  try {
    await sensorsStore.fetchSensors()
  } catch {
    // The store exposes the error state to the view
  }
}

async function loadAlerts() {
  try {
    await alertsStore.fetchAlerts()
  } catch {
    // Only the "alerts in 7 days" figure depends on it: it shows '—'
  }
}

// Worst buildings first, then by name
const STATUS_ORDER = { CRITICAL: 0, WARNING: 1, OK: 2 }
const sortedSites = computed(() =>
  [...sites.value].sort(
    (a, b) => (STATUS_ORDER[a.status] ?? 3) - (STATUS_ORDER[b.status] ?? 3) || a.name.localeCompare(b.name, 'es'),
  ),
)

function alertingIn(siteId) {
  if (sensorsStore.status !== 'success') return '—'
  return sensorsStore.sensors.filter(
    (sensor) => sensor.site_id === siteId && ['WARNING', 'CRITICAL'].includes(sensor.health),
  ).length
}

function floorsText(item) {
  return item.basements > 0 ? `${item.floors} + ${item.basements}` : `${item.floors}`
}

// ---------------------------------------------------------------------------
// Open building: the one in the URL, or the only one when there is just one
// ---------------------------------------------------------------------------
const siteId = computed(() => {
  const fromUrl = route.query.site
  if (fromUrl && sitesStore.siteById(fromUrl)) return fromUrl
  return sites.value.length === 1 ? sites.value[0].id : null
})

const site = computed(() => (siteId.value ? sitesStore.siteById(siteId.value) : null))

function openSite(id) {
  const query = { ...route.query }
  if (id) query.site = id
  else delete query.site
  router.push({ query })
}

const siteSensors = computed(() => sensorsStore.sensors.filter((sensor) => sensor.site_id === siteId.value))

// "Av. Diagonal 19 · 4 plantas + 2 sótanos · 8 sensores"
const siteSummary = computed(() => {
  const s = site.value
  const parts = []
  if (s.address) parts.push(s.address)
  parts.push(
    `${s.floors} ${s.floors === 1 ? 'planta' : 'plantas'}` +
      (s.basements > 0 ? ` + ${s.basements} ${s.basements === 1 ? 'sótano' : 'sótanos'}` : ''),
  )
  parts.push(`${siteSensors.value.length} ${siteSensors.value.length === 1 ? 'sensor' : 'sensores'}`)
  return parts.join(' · ')
})

// ---------------------------------------------------------------------------
// Selected sensor and its 7-day series (B7)
// ---------------------------------------------------------------------------
const selectedId = ref(null)
const sidePanel = ref(null)
const selectedSensor = computed(() => siteSensors.value.find((sensor) => sensor.id === selectedId.value) ?? null)

function selectSensor(id) {
  selectedId.value = id
  // On small screens the panel is below the building: bring it into view
  nextTick(() => {
    if (window.matchMedia?.('(max-width: 1023px)').matches) {
      sidePanel.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  })
}

// When a building opens, show its most worrying sensor straight away
const HEALTH_ORDER = { CRITICAL: 0, WARNING: 1, OFFLINE: 2, OK: 3 }
function defaultSensorId() {
  const [first] = [...siteSensors.value].sort(
    (a, b) => (HEALTH_ORDER[a.health] ?? 4) - (HEALTH_ORDER[b.health] ?? 4),
  )
  return first?.id ?? null
}

const readings = ref([])
const readingsLoading = ref(false)
const readingsError = ref('')

// silent: refresh without the spinner, keeping the chart if it fails
async function loadReadings({ silent = false } = {}) {
  const sensorId = selectedId.value
  if (!sensorId) return
  if (!silent) {
    readingsLoading.value = true
    readingsError.value = ''
    readings.value = []
  }
  try {
    const response = await readingService.getSensorSeries(sensorId, { days: 7 })
    if (selectedId.value !== sensorId) return
    // PressureChart takes ReadingResponse-like points: the bucket average
    readings.value = (response.data.points ?? []).map((point) => ({
      pressure: point.avg,
      measured_at: point.t,
    }))
    readingsError.value = ''
  } catch (err) {
    if (selectedId.value !== sensorId || silent) return
    readingsError.value = err?.message || 'No se han podido cargar las lecturas.'
  } finally {
    if (selectedId.value === sensorId) readingsLoading.value = false
  }
}

watch(selectedId, () => loadReadings())

// Alerts of the selected sensor in the last 7 days
const alertCount = computed(() => {
  // During a refresh the previous list is still valid
  const ready = alertsStore.status === 'success' || (alertsStore.status === 'loading' && alertsStore.alerts.length)
  if (!selectedId.value || !ready) return null
  const since = Date.now() - 7 * DAY_MS
  return alertsStore.alerts.filter(
    (alert) => alert.sensor_id === selectedId.value && new Date(alert.created_at).getTime() >= since,
  ).length
})

// ---------------------------------------------------------------------------
// Alerts of the week (B9)
// ---------------------------------------------------------------------------
const weekly = ref(null)
const weeklyLoading = ref(false)
const weeklyError = ref('')

async function loadWeekly({ silent = false } = {}) {
  const id = siteId.value
  if (!id) return
  if (!silent) {
    weeklyLoading.value = true
    weeklyError.value = ''
    weekly.value = null
  }
  try {
    const response = await analyticsService.getWeeklyAlerts({ site_id: id })
    if (siteId.value !== id) return
    weekly.value = response.data
    weeklyError.value = ''
  } catch (err) {
    if (siteId.value !== id || silent) return
    weeklyError.value = err?.message || 'No se han podido cargar las alertas de la semana.'
  } finally {
    if (siteId.value === id) weeklyLoading.value = false
  }
}

// Another building (or the first load): reset the sensor and load its week
watch(
  siteId,
  (id) => {
    selectedId.value = null
    weekly.value = null
    if (!id) return
    loadWeekly()
  },
  { immediate: true },
)

// Pick the default sensor once the building and its sensors are known
watch(
  () => [siteId.value, siteSensors.value.length],
  () => {
    if (siteId.value && !selectedSensor.value) selectedId.value = defaultSensorId()
  },
  { immediate: true },
)

// ---------------------------------------------------------------------------
// Loading and auto refresh (every minute and when the tab is visible again)
// ---------------------------------------------------------------------------
function loadAll() {
  return Promise.all([loadSites(), loadSensors(), loadAlerts()])
}

function refresh() {
  return Promise.all([
    loadAll(),
    loadWeekly({ silent: true }),
    loadReadings({ silent: true }),
  ])
}

useAutoRefresh(refresh, REFRESH_MS)

onMounted(loadAll)
</script>
