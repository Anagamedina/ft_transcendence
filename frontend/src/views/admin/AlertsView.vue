
<template>
  <section class="space-y-6">
    <header class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Alertas</h1>
        <p class="mt-1 text-sm text-slate-500">
          Consulta y gestiona las alertas de los sensores.
        </p>
      </div>

      <button
        type="button"
        class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium hover:bg-slate-50"
        :disabled="status === 'loading'"
        @click="loadAlerts"
      >
        Actualizar
      </button>
    </header>

    <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <div class="rounded-xl border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Total</p>
        <p class="mt-1 text-2xl font-semibold">{{ alerts.length }}</p>
      </div>
      <div class="rounded-xl border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Activas</p>
        <p class="mt-1 text-2xl font-semibold">{{ activeCount }}</p>
      </div>
      <div class="rounded-xl border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Críticas</p>
        <p class="mt-1 text-2xl font-semibold">{{ criticalCount }}</p>
      </div>
    </div>

    <div class="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 md:flex-row">
      <input
        v-model.trim="search"
        type="search"
        placeholder="Buscar por mensaje o sensor..."
        aria-label="Buscar alertas"
        class="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
      />

      <select
        v-model="statusFilter"
        aria-label="Filtrar por estado"
        class="rounded-lg border border-slate-300 px-3 py-2 text-sm"
      >
        <option value="ALL">Todos los estados</option>
        <option value="ACTIVE">Activas</option>
        <option value="RESOLVED">Resueltas</option>
      </select>

      <select
        v-model="severityFilter"
        aria-label="Filtrar por severidad"
        class="rounded-lg border border-slate-300 px-3 py-2 text-sm"
      >
        <option value="ALL">Todas las severidades</option>
        <option value="CRITICAL">Crítica</option>
        <option value="WARNING">Advertencia</option>
        <option value="INFO">Informativa</option>
      </select>

      <button
        type="button"
        class="rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-slate-100"
        @click="resetFilters"
      >
        Limpiar filtros
      </button>
    </div>

    <div
      v-if="actionError"
      class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
      role="alert"
    >
      {{ actionError }}
    </div>

    <div
      v-if="status === 'loading' || status === 'idle'"
      class="rounded-xl border border-slate-200 bg-white p-10 text-center text-slate-600"
      role="status"
    >
      Cargando alertas...
    </div>

    <div
      v-else-if="status === 'error'"
      class="rounded-xl border border-red-200 bg-white p-6"
      role="alert"
    >
      <h2 class="font-semibold text-red-700">No se pudieron cargar las alertas</h2>
      <p class="mt-2 text-sm text-slate-600">
        {{ error?.message || 'Se ha producido un error inesperado.' }}
      </p>
      <button
        type="button"
        class="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
        @click="loadAlerts"
      >
        Reintentar
      </button>
    </div>

    <div
      v-else-if="alerts.length === 0"
      class="rounded-xl border border-slate-200 bg-white p-10 text-center"
    >
      <h2 class="font-semibold text-slate-800">No hay alertas registradas</h2>
      <p class="mt-2 text-sm text-slate-500">
        Cuando haya alertas disponibles, aparecerán aquí.
      </p>
    </div>

    <div
      v-else-if="filteredAlerts.length === 0"
      class="rounded-xl border border-slate-200 bg-white p-10 text-center"
    >
      <h2 class="font-semibold text-slate-800">No hay resultados</h2>
      <p class="mt-2 text-sm text-slate-500">
        Prueba a cambiar los filtros de búsqueda.
      </p>
      <button
        type="button"
        class="mt-3 text-sm font-medium text-aqua-800 underline"
        @click="resetFilters"
      >
        Limpiar filtros
      </button>
    </div>

    <div
      v-else
      class="overflow-x-auto rounded-xl border border-slate-200 bg-white"
    >
      <table class="min-w-full divide-y divide-slate-200 text-left text-sm">
        <thead class="bg-slate-50 text-slate-600">
          <tr>
            <th scope="col" class="px-4 py-3 font-medium">Alerta</th>
            <th scope="col" class="px-4 py-3 font-medium">Tipo</th>
            <th scope="col" class="px-4 py-3 font-medium">Sensor</th>
            <th scope="col" class="px-4 py-3 font-medium">Severidad</th>
            <th scope="col" class="px-4 py-3 font-medium">Estado</th>
            <th scope="col" class="px-4 py-3 font-medium">Fecha</th>
            <th scope="col" class="px-4 py-3 font-medium">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="alert in filteredAlerts" :key="alert.id">
            <td class="min-w-64 px-4 py-3 text-slate-800">
              {{ alert.message || '—' }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-slate-600">
              {{ alert.type || '—' }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 font-mono text-xs text-slate-600">
              {{ sensorName(alert.sensor_id) }}
            </td>
            <td class="whitespace-nowrap px-4 py-3">
              <span
                class="rounded-full px-2.5 py-1 text-xs font-medium"
                :class="severityClass(alert.severity)"
              >
                {{ severityLabel(alert.severity) }}
              </span>
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-slate-600">
              {{ alert.status === 'ACTIVE' ? 'Activa' : alert.status === 'RESOLVED' ? 'Resuelta' : alert.status || '—' }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-slate-600">
              {{ formatDate(alert.created_at) }}
            </td>
            <td class="whitespace-nowrap px-4 py-3">
              <div class="flex flex-wrap gap-2">
                <button
                  v-if="alert.status === 'ACTIVE' && !alert.acknowledged_at"
                  type="button"
                  class="rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-medium hover:bg-slate-50 disabled:opacity-50"
                  :disabled="busyAlertId === alert.id"
                  @click="acknowledge(alert.id)"
                >
                  Acusar recibo
                </button>
                <button
                  v-if="alert.status === 'ACTIVE'"
                  type="button"
                  class="rounded-md bg-aqua-900 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-aqua-800 disabled:opacity-50"
                  :disabled="busyAlertId === alert.id"
                  @click="resolve(alert.id)"
                >
                  Resolver
                </button>
                <span
                  v-if="alert.status === 'RESOLVED'"
                  class="text-xs text-slate-500"
                >
                  Sin acciones
                </span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <p class="border-t border-slate-100 px-4 py-3 text-sm text-slate-500">
        {{ filteredAlerts.length }} de {{ alerts.length }} alertas
      </p>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAlertsStore } from '../../stores/alerts.js'
import { useSensorsStore } from '../../stores/sensors.js'

const alertStore = useAlertsStore()
const sensorStore = useSensorsStore()

const search = ref('')
const statusFilter = ref('ALL')
const severityFilter = ref('ALL')
const busyAlertId = ref(null)
const actionError = ref('')

const alerts = computed(() => alertStore.alerts)
const status = computed(() => alertStore.status)
const error = computed(() => alertStore.error)
const sensors = computed(() => sensorStore.sensors)

const activeCount = computed(
  () => alerts.value.filter((alert) => alert.status === 'ACTIVE').length
)

const criticalCount = computed(
  () => alerts.value.filter(
    (alert) => alert.severity === 'CRITICAL' && alert.status === 'ACTIVE'
  ).length
)

const filteredAlerts = computed(() => {
  const query = search.value.toLocaleLowerCase()

  return alerts.value.filter((alert) => {
    const matchesSearch = [
      alert.message,
      alert.type,
      alert.sensor_id,
      sensorName(alert.sensor_id),
    ].some((value) =>
      String(value ?? '').toLocaleLowerCase().includes(query)
    )

    const matchesStatus =
      statusFilter.value === 'ALL' ||
      alert.status === statusFilter.value

    const matchesSeverity =
      severityFilter.value === 'ALL' ||
      alert.severity === severityFilter.value

    return matchesSearch && matchesStatus && matchesSeverity
  })
})

async function loadAlerts() {
  try {
    await alertStore.fetchAlerts()
  } catch {
    // The store exposes the error state to the view.
  }
}

async function loadSensors() {
  if (sensorStore.status === 'success') return

  try {
    await sensorStore.fetchSensors()
  } catch {
    // Sensor names fall back to their IDs if loading fails.
  }
}

async function acknowledge(id) {
  busyAlertId.value = id
  actionError.value = ''

  try {
    await alertStore.acknowledgeAlert(id)
  } catch (err) {
    actionError.value = err?.message || 'No se pudo acusar recibo de la alerta.'
  } finally {
    busyAlertId.value = null
  }
}

async function resolve(id) {
  busyAlertId.value = id
  actionError.value = ''

  try {
    await alertStore.resolveAlert(id)
  } catch (err) {
    actionError.value = err?.message || 'No se pudo resolver la alerta.'
  } finally {
    busyAlertId.value = null
  }
}

function resetFilters() {
  search.value = ''
  statusFilter.value = 'ALL'
  severityFilter.value = 'ALL'
}

function sensorName(id) {
  const sensor = sensors.value.find((item) => item.id === id)
  return sensor?.name || id || '—'
}

function severityLabel(severity) {
  const labels = {
    CRITICAL: 'Crítica',
    WARNING: 'Advertencia',
    INFO: 'Informativa',
  }

  return labels[severity] || severity || '—'
}

function severityClass(severity) {
  const classes = {
    CRITICAL: 'bg-red-100 text-red-800',
    WARNING: 'bg-amber-100 text-amber-800',
    INFO: 'bg-blue-100 text-blue-800',
  }

  return classes[severity] || 'bg-slate-100 text-slate-700'
}

function formatDate(value) {
  if (!value) return '—'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return '—'

  return new Intl.DateTimeFormat('es-ES', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(date)
}

onMounted(() => {
  loadAlerts()
  loadSensors()
})
</script>
