<!--
  ADMIN SENSORS VIEW (#169)
  As in the A-Sensores mockup: building selector, the building floor by floor
  (BuildingStack) and, next to it, the selected sensor (SensorDetailPanel) or
  SensorForm to create a sensor or adjust its floor and thresholds.
  Below, every sensor of every client in a DataTable.
  /admin/sensors?site=<id> opens that building (link from the sites view).
  Rendered inside AdminLayout.
-->

<template>
  <AdminLayout>
    <section class="space-y-6">
      <!-- Title, building selector and "+ Nuevo sensor" -->
      <header class="flex flex-wrap items-end justify-between gap-4">
        <div class="min-w-0">
          <h1 class="text-2xl font-bold text-slate-900">Sensores</h1>
          <p v-if="site" class="mt-1 text-sm text-slate-600">{{ siteSummary }}</p>
        </div>

        <div class="flex flex-wrap items-end gap-2">
          <div class="flex flex-col gap-1">
            <label for="sensors-site" class="text-[13px] font-medium text-slate-600">Edificio</label>
            <select
              id="sensors-site"
              :value="siteId"
              class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm sm:w-80"
              :disabled="siteOptions.length === 0"
              @change="chooseSite($event.target.value)"
            >
              <option v-for="option in siteOptions" :key="option.id" :value="option.id">
                {{ option.label }}
              </option>
            </select>
          </div>
          <button
            type="button"
            class="min-h-10 rounded-lg bg-aqua-600 px-4 text-sm font-semibold text-white hover:bg-aqua-700 disabled:opacity-50"
            :disabled="!site || sensorsLoading"
            @click="openCreate"
          >
            + Nuevo sensor
          </button>
        </div>
      </header>

      <!-- Building floor by floor + detail or form -->
      <LoadingState v-if="sitesLoading || (site && sensorsLoading)" message="Cargando edificio…" />
      <ErrorState v-else-if="sitesError" :message="sitesError" @retry="loadAll" />
      <ErrorState v-else-if="sensorsError" :message="sensorsError" @retry="loadSensors" />
      <EmptyState
        v-else-if="!site"
        icon="building"
        title="No hay edificios registrados"
        message="Da de alta un edificio en la página de edificios para instalar sensores."
      />

      <div v-else class="grid items-start gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <BuildingStack
          :name="site.name"
          :floors="site.floors"
          :basements="site.basements"
          :sensors="siteSensors"
          :selected-id="selectedId"
          @select="selectSensor"
        />

        <div ref="sidePanel" class="space-y-3">
          <!-- Create or edit: SensorForm -->
          <section
            v-if="formMode"
            class="flex flex-col gap-4 rounded-xl border border-slate-200 bg-white p-5"
            :aria-labelledby="'sensor-form-title'"
          >
            <div>
              <p class="text-xs font-bold uppercase tracking-[0.08em] text-aqua-700">
                {{ formMode === 'create' ? 'Nuevo sensor' : 'Ajustar sensor' }}
              </p>
              <h2 id="sensor-form-title" class="text-lg font-bold text-aqua-900">
                {{ formMode === 'create' ? site.name : selectedSensor?.name }}
              </h2>
            </div>

            <form id="sensor-form" novalidate class="space-y-4" @submit.prevent="save">
              <SensorForm
                ref="sensorForm"
                v-model="form"
                :floors="site.floors"
                :basements="site.basements"
                :mode="formMode"
                :taken-labels="siteSensors.map((sensor) => sensor.external_id)"
              />
              <p v-if="saveError" role="alert" class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
                {{ saveError }}
              </p>
            </form>

            <div class="flex justify-end gap-2 border-t border-slate-200 pt-4">
              <button
                type="button"
                class="min-h-10 rounded-lg border border-slate-300 px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                :disabled="saving"
                @click="closeForm"
              >
                Cancelar
              </button>
              <button
                type="submit"
                form="sensor-form"
                class="min-h-10 rounded-lg bg-aqua-600 px-4 text-sm font-semibold text-white hover:bg-aqua-700 disabled:opacity-50"
                :disabled="saving"
              >
                {{ saving ? 'Guardando…' : 'Guardar sensor' }}
              </button>
            </div>
          </section>

          <!-- Selected sensor: detail with the pressure chart -->
          <template v-else-if="selectedSensor">
            <SensorDetailPanel
              :sensor="selectedSensor"
              :readings="readings"
              :alert-count="alertCount"
              :loading="readingsLoading"
              :error="readingsError"
              @retry="loadReadings"
            />
            <button
              type="button"
              class="min-h-10 w-full rounded-lg border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              @click="openEdit"
            >
              Ajustar planta y umbrales
            </button>
          </template>

          <EmptyState
            v-else-if="siteSensors.length > 0"
            icon="droplet"
            title="Elige un sensor"
            message="Toca un sensor del edificio para ver su detalle y ajustar sus umbrales."
            compact
          />
        </div>
      </div>

      <!-- Every sensor of every client -->
      <section class="space-y-4 pt-2" aria-labelledby="all-sensors-title">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h2 id="all-sensors-title" class="text-lg font-bold text-slate-900">Todos los sensores</h2>
          <button
            type="button"
            class="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50"
            :disabled="sensorsLoading"
            @click="loadSensors"
          >
            Actualizar
          </button>
        </div>

        <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div class="rounded-xl border border-slate-200 bg-white p-4">
            <p class="text-sm text-slate-500">Total</p>
            <p class="mt-1 text-2xl font-semibold">{{ sensors.length }}</p>
          </div>
          <div class="rounded-xl border border-slate-200 bg-white p-4">
            <p class="text-sm text-slate-500">Con alertas</p>
            <p class="mt-1 text-2xl font-semibold">{{ alertingCount }}</p>
          </div>
          <div class="rounded-xl border border-slate-200 bg-white p-4">
            <p class="text-sm text-slate-500">Sin conexión</p>
            <p class="mt-1 text-2xl font-semibold">{{ offlineCount }}</p>
          </div>
        </div>

        <DataTable
          :columns="COLUMNS"
          :rows="sensors"
          :search-fields="['name', 'external_id', 'site_name', 'organization_name']"
          search-placeholder="Sensor, etiqueta, edificio o cliente…"
          :filters="filters"
          :loading="sensorsLoading"
          :error="sensorsError"
          item-name="sensores"
          empty-title="No hay sensores registrados"
          empty-message="Elige un edificio arriba y pulsa «Nuevo sensor»."
          icon="droplet"
          caption="Todos los sensores"
          @retry="loadSensors"
        >
          <template #row="{ row: sensor }">
            <tr>
              <td class="px-4 py-3">
                <!-- Opens the sensor in the building above -->
                <button
                  type="button"
                  class="text-left font-semibold text-aqua-700 hover:underline"
                  @click="showSensor(sensor)"
                >
                  {{ sensor.name }}
                </button>
                <span class="block text-xs text-slate-500">{{ sensor.external_id }}</span>
              </td>
              <td class="px-4 py-3 text-slate-600">
                {{ sensor.site_name }}
                <span class="block text-xs text-slate-500">{{ sensor.organization_name }}</span>
              </td>
              <td class="whitespace-nowrap px-4 py-3 text-slate-600">{{ floorLabel(sensor.floor ?? 0) }}</td>
              <td class="whitespace-nowrap px-4 py-3 text-right tabular-nums text-slate-600">
                {{ formatValue(sensor.last_value, sensor.unit) }}
              </td>
              <td class="whitespace-nowrap px-4 py-3 tabular-nums text-slate-600">
                {{ formatRange(sensor) }}
              </td>
              <td class="px-4 py-3">
                <StatusPill type="SensorHealth" :value="sensor.health" />
              </td>
              <td class="whitespace-nowrap px-4 py-3 text-slate-600">{{ formatDate(sensor.last_seen_at) }}</td>
            </tr>
          </template>
        </DataTable>
      </section>
    </section>
  </AdminLayout>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminLayout from '../../layouts/AdminLayout.vue'
import BuildingStack from '../../components/BuildingStack.vue'
import SensorDetailPanel from '../../components/SensorDetailPanel.vue'
import SensorForm, { emptySensor } from '../../components/SensorForm.vue'
import DataTable from '../../components/DataTable.vue'
import StatusPill from '../../components/StatusPill.vue'
import LoadingState from '../../components/LoadingState.vue'
import ErrorState from '../../components/ErrorState.vue'
import EmptyState from '../../components/EmptyState.vue'
import { useSitesStore } from '../../stores/sites.js'
import { useSensorsStore } from '../../stores/sensors.js'
import { useReadingsStore } from '../../stores/readings.js'
import { useAlertsStore } from '../../stores/alerts.js'
import { useLabels } from '../../composables/useLabels'
import { floorLabel } from '../../utils/floors'

const route = useRoute()
const router = useRouter()
const sitesStore = useSitesStore()
const sensorsStore = useSensorsStore()
const readingsStore = useReadingsStore()
const alertsStore = useAlertsStore()
const { label } = useLabels()

// ---------------------------------------------------------------------------
// Loading
// ---------------------------------------------------------------------------
const sitesLoading = computed(() => ['idle', 'loading'].includes(sitesStore.status))
const sensorsLoading = computed(() => ['idle', 'loading'].includes(sensorsStore.status))

const sitesError = computed(() =>
  sitesStore.status === 'error' ? sitesStore.error?.message || 'No se han podido cargar los edificios.' : ''
)
const sensorsError = computed(() =>
  sensorsStore.status === 'error' ? sensorsStore.error?.message || 'No se han podido cargar los sensores.' : ''
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

function loadAll() {
  return Promise.all([loadSites(), loadSensors()])
}

// ---------------------------------------------------------------------------
// Selected building. It lives in the URL (?site=<id>), so the link from the
// sites view, reloading the page and the back button all keep it.
// ---------------------------------------------------------------------------

// "Edificio principal · Hotel Diagonal Mar", sorted by client and then by name
const siteOptions = computed(() =>
  [...sitesStore.sites]
    .sort(
      (a, b) =>
        a.organization_name.localeCompare(b.organization_name, 'es') || a.name.localeCompare(b.name, 'es')
    )
    .map((option) => ({ id: option.id, label: `${option.name} · ${option.organization_name}` }))
)

// The building in the URL, or the first one of the list when there is none (or it no longer exists)
const siteId = computed(() => {
  const fromUrl = route.query.site
  if (fromUrl && sitesStore.siteById(fromUrl)) return fromUrl
  return siteOptions.value[0]?.id ?? null
})

const site = computed(() => (siteId.value ? sitesStore.siteById(siteId.value) : null))

function chooseSite(id) {
  router.replace({ query: { ...route.query, site: id } })
}

// Sensors of the selected building, taken from the full list: creating or
// editing a sensor updates the building and the table at the same time
const siteSensors = computed(() => sensorsStore.sensors.filter((sensor) => sensor.site_id === siteId.value))

// "Sant Martí · 4 plantas + 2 sótanos · 8 sensores" as in the mockup.
// The district only appears once the API returns it (D10).
const siteSummary = computed(() => {
  const s = site.value
  const parts = []
  if (s.district) parts.push(label('District', s.district))
  parts.push(
    `${s.floors} ${s.floors === 1 ? 'planta' : 'plantas'}` +
      (s.basements > 0 ? ` + ${s.basements} ${s.basements === 1 ? 'sótano' : 'sótanos'}` : '')
  )
  parts.push(`${siteSensors.value.length} ${siteSensors.value.length === 1 ? 'sensor' : 'sensores'}`)
  return parts.join(' · ')
})

// ---------------------------------------------------------------------------
// Selected sensor and its detail
// ---------------------------------------------------------------------------
const selectedId = ref(null)
const sidePanel = ref(null)

const selectedSensor = computed(() => siteSensors.value.find((sensor) => sensor.id === selectedId.value) ?? null)

function selectSensor(id) {
  if (saving.value) return
  formMode.value = null
  selectedId.value = id
}

// From the table: open its building and select it, then bring the panel into view
function showSensor(sensor) {
  if (sensor.site_id !== siteId.value) chooseSite(sensor.site_id)
  selectSensor(sensor.id)
  nextTick(() => sidePanel.value?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
}

// Another building: nothing selected and no open form
watch(siteId, () => {
  selectedId.value = null
  formMode.value = null
})

const readings = computed(() => readingsStore.readings)
const readingsLoading = computed(() => readingsStore.status === 'loading')
const readingsError = computed(() =>
  readingsStore.status === 'error' ? readingsStore.error?.message || 'No se han podido cargar las lecturas.' : ''
)

function loadReadings() {
  if (selectedId.value) readingsStore.fetchReadings(selectedId.value)
}

// The chart follows the selected sensor
watch(selectedId, loadReadings)

// Alerts of the selected sensor in the last 7 days. The admin menu already
// loads the alerts, so this needs no extra request.
const DAY_MS = 24 * 60 * 60 * 1000
const alertCount = computed(() => {
  if (!selectedId.value || alertsStore.status !== 'success') return null
  const since = Date.now() - 7 * DAY_MS
  return alertsStore.alerts.filter(
    (alert) => alert.sensor_id === selectedId.value && new Date(alert.created_at).getTime() >= since
  ).length
})

// ---------------------------------------------------------------------------
// Create / edit form (SensorForm)
// ---------------------------------------------------------------------------
// null | 'create' | 'edit'
const formMode = ref(null)
const form = ref(emptySensor())
const sensorForm = ref(null)
const saving = ref(false)
const saveError = ref('')

// Fields that PATCH /api/sensors/{id} accepts and this form edits
const EDITABLE = ['name', 'floor', 'min_pressure', 'max_pressure']

function openCreate() {
  // No sensor highlighted while a new one is being created
  selectedId.value = null
  form.value = emptySensor()
  saveError.value = ''
  formMode.value = 'create'
  nextTick(() => sidePanel.value?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
}

function openEdit() {
  const s = selectedSensor.value
  form.value = {
    name: s.name,
    floor: s.floor ?? 0,
    min_pressure: s.min_pressure,
    max_pressure: s.max_pressure,
  }
  saveError.value = ''
  formMode.value = 'edit'
}

function closeForm() {
  if (saving.value) return
  formMode.value = null
}

async function save() {
  saveError.value = ''
  if (!sensorForm.value.validate()) return

  saving.value = true
  try {
    if (formMode.value === 'create') {
      const created = await sensorsStore.createSensor({
        site_id: site.value.id,
        external_id: form.value.external_id.trim(),
        name: form.value.name.trim(),
        floor: form.value.floor,
        min_pressure: form.value.min_pressure,
        max_pressure: form.value.max_pressure,
      })
      selectedId.value = created.id
    } else {
      // PATCH sends only what changed
      const data = { ...form.value, name: form.value.name.trim() }
      const changes = Object.fromEntries(
        EDITABLE.filter((field) => data[field] !== selectedSensor.value[field]).map((field) => [field, data[field]])
      )
      if (Object.keys(changes).length > 0) {
        await sensorsStore.updateSensor(selectedSensor.value.id, changes)
      }
    }
    formMode.value = null
  } catch (err) {
    // The API explains the problem: repeated device label (409), floor outside
    // the building (FLOOR_OUT_OF_SITE), thresholds... Show it as it comes.
    saveError.value = err?.message || 'No se ha podido guardar el sensor.'
  } finally {
    saving.value = false
  }
}

// ---------------------------------------------------------------------------
// Table of every sensor
// ---------------------------------------------------------------------------
const COLUMNS = [
  { key: 'name', label: 'Sensor' },
  { key: 'site_name', label: 'Edificio' },
  { key: 'floor', label: 'Planta' },
  { key: 'last_value', label: 'Valor' },
  { key: 'range', label: 'Rango permitido' },
  { key: 'health', label: 'Estado' },
  { key: 'last_seen_at', label: 'Última lectura' },
]

const sensors = computed(() => sensorsStore.sensors)

const alertingCount = computed(
  () => sensors.value.filter((sensor) => sensor.health === 'WARNING' || sensor.health === 'CRITICAL').length
)
const offlineCount = computed(() => sensors.value.filter((sensor) => sensor.health === 'OFFLINE').length)

// Clients that have sensors, for the client filter
const clientOptions = computed(() => {
  const byId = new Map()
  for (const sensor of sensors.value) byId.set(sensor.organization_id, sensor.organization_name)
  return [...byId]
    .map(([value, text]) => ({ value, label: text }))
    .sort((a, b) => a.label.localeCompare(b.label, 'es'))
})

const filters = computed(() => [
  {
    key: 'health',
    label: 'Estado',
    allLabel: 'Todos los estados',
    options: ['OK', 'WARNING', 'CRITICAL', 'OFFLINE'].map((value) => ({
      value,
      label: label('SensorHealth', value),
    })),
  },
  {
    key: 'organization_id',
    label: 'Cliente',
    allLabel: 'Todos los clientes',
    options: clientOptions.value,
  },
])

// Spanish number format: '4,2 bar' and '2,0–6,0 bar'
const oneDecimal = new Intl.NumberFormat('es-ES', { minimumFractionDigits: 1, maximumFractionDigits: 1 })

function formatValue(value, unit) {
  return value === null || value === undefined ? '—' : `${oneDecimal.format(value)} ${unit || 'bar'}`
}

function formatRange(sensor) {
  return `${oneDecimal.format(sensor.min_pressure)}–${oneDecimal.format(sensor.max_pressure)} ${sensor.unit || 'bar'}`
}

// Short Spanish date and time, e.g. "8/9/26, 10:30"
const dateFormat = new Intl.DateTimeFormat('es-ES', { dateStyle: 'short', timeStyle: 'short' })

function formatDate(value) {
  if (!value) return 'Nunca'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '—' : dateFormat.format(date)
}

onMounted(loadAll)
</script>
