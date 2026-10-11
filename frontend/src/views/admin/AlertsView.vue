<template>
  <AdminLayout>
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

    <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <div class="rounded-xl border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Sin reconocer</p>
        <p class="mt-1 text-2xl font-semibold">{{ pendingCount }}</p>
      </div>
      <div class="rounded-xl border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Reconocidas</p>
        <p class="mt-1 text-2xl font-semibold">{{ acknowledgedCount }}</p>
      </div>
      <div class="rounded-xl border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Críticas abiertas</p>
        <p class="mt-1 text-2xl font-semibold">{{ criticalCount }}</p>
      </div>
      <div class="rounded-xl border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Resueltas</p>
        <p class="mt-1 text-2xl font-semibold">{{ resolvedCount }}</p>
      </div>
    </div>

    <div
      v-if="sensorRanking.length > 0"
      class="rounded-xl border border-slate-200 bg-white p-4"
    >
      <h2 class="text-sm font-semibold text-slate-800">Sensores con más alertas</h2>
      <ol class="mt-3 divide-y divide-slate-100 text-sm">
        <li
          v-for="(sensor, index) in sensorRanking"
          :key="sensor.id"
          class="flex items-center gap-3 py-2"
        >
          <span class="w-5 text-slate-400">{{ index + 1 }}</span>
          <span class="min-w-0 flex-1 truncate text-slate-800">
            {{ sensor.name }}
            <span class="text-slate-500">· {{ sensor.site }}</span>
          </span>
          <span class="font-semibold text-slate-900">{{ sensor.total }}</span>
        </li>
      </ol>
    </div>

    <div class="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 md:flex-row">
      <input
        v-model.trim="search"
        type="search"
        placeholder="Buscar por mensaje, sensor o cliente..."
        aria-label="Buscar alertas"
        class="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
      />

      <select
        v-model="clientFilter"
        aria-label="Filtrar por cliente"
        class="rounded-lg border border-slate-300 px-3 py-2 text-sm"
      >
        <option value="ALL">Todos los clientes</option>
        <option v-for="client in clients" :key="client.id" :value="client.id">
          {{ client.name }}
        </option>
      </select>

      <select
        v-model="stateFilter"
        aria-label="Filtrar por estado"
        class="rounded-lg border border-slate-300 px-3 py-2 text-sm"
      >
        <option value="ALL">Todos los estados</option>
        <option value="ACTIVE">Sin reconocer</option>
        <option value="ACKNOWLEDGED">Reconocidas</option>
        <option value="RESOLVED">Resueltas</option>
      </select>

      <select
        v-model="severityFilter"
        aria-label="Filtrar por gravedad"
        class="rounded-lg border border-slate-300 px-3 py-2 text-sm"
      >
        <option value="ALL">Todas las gravedades</option>
        <option value="CRITICAL">Crítica</option>
        <option value="WARNING">Advertencia</option>
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
            <th scope="col" class="px-4 py-3 font-medium">Cliente</th>
            <th scope="col" class="px-4 py-3 font-medium">Sensor</th>
            <th scope="col" class="px-4 py-3 font-medium">Gravedad</th>
            <th scope="col" class="px-4 py-3 font-medium">Estado</th>
            <th scope="col" class="px-4 py-3 font-medium">Fecha</th>
            <th scope="col" class="px-4 py-3 font-medium">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="alert in filteredAlerts" :key="alert.id">
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
              <span
                class="rounded-full px-2.5 py-1 text-xs font-medium"
                :class="severityClass(alert.severity)"
              >
                {{ severityLabel(alert.severity) }}
              </span>
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-slate-600">
              {{ stateLabel(alert.state) }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-slate-600">
              {{ formatDate(alert.created_at) }}
            </td>
            <td class="whitespace-nowrap px-4 py-3">
              <div class="flex flex-wrap gap-2">
                <button
                  v-if="alert.state === 'ACTIVE'"
                  type="button"
                  class="rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-medium hover:bg-slate-50 disabled:opacity-50"
                  :disabled="busyAlertId === alert.id"
                  @click="acknowledge(alert.id)"
                >
                  Reconocer
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
  </AdminLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import AdminLayout from '../../layouts/AdminLayout.vue'
import { useAlertsStore } from '../../stores/alerts.js'

const alertStore = useAlertsStore()

const search = ref('')
const clientFilter = ref('ALL')
const stateFilter = ref('ALL')
const severityFilter = ref('ALL')
const busyAlertId = ref(null)
const actionError = ref('')

const alerts = computed(() => alertStore.alerts)
const status = computed(() => alertStore.status)
const error = computed(() => alertStore.error)

const pendingCount = computed(
  () => alerts.value.filter((alert) => alert.state === 'ACTIVE').length
)

const acknowledgedCount = computed(
  () => alerts.value.filter((alert) => alert.state === 'ACKNOWLEDGED').length
)

const resolvedCount = computed(
  () => alerts.value.filter((alert) => alert.state === 'RESOLVED').length
)

const criticalCount = computed(
  () => alerts.value.filter(
    (alert) => alert.severity === 'CRITICAL' && alert.status === 'ACTIVE'
  ).length
)

const clients = computed(() => {
  const names = new Map()

  for (const alert of alerts.value) {
    names.set(alert.organization_id, alert.organization_name)
  }

  return [...names]
    .map(([id, name]) => ({ id, name }))
    .sort((a, b) => a.name.localeCompare(b.name))
})

const sensorRanking = computed(() => {
  const sensors = new Map()

  for (const alert of alerts.value) {
    const sensor = sensors.get(alert.sensor_id) || {
      id: alert.sensor_id,
      name: alert.sensor_name,
      site: alert.site_name,
      total: 0,
    }

    sensor.total += 1
    sensors.set(alert.sensor_id, sensor)
  }

  return [...sensors.values()]
    .sort((a, b) => b.total - a.total)
    .slice(0, 5)
})

const filteredAlerts = computed(() => {
  const query = search.value.toLocaleLowerCase()

  return alerts.value.filter((alert) => {
    const matchesSearch = [
      alert.message,
      alert.type,
      alert.sensor_name,
      alert.site_name,
      alert.organization_name,
    ].some((value) =>
      String(value ?? '').toLocaleLowerCase().includes(query)
    )

    const matchesClient =
      clientFilter.value === 'ALL' ||
      alert.organization_id === clientFilter.value

    const matchesState =
      stateFilter.value === 'ALL' ||
      alert.state === stateFilter.value

    const matchesSeverity =
      severityFilter.value === 'ALL' ||
      alert.severity === severityFilter.value

    return matchesSearch && matchesClient && matchesState && matchesSeverity
  })
})

async function loadAlerts() {
  try {
    await alertStore.fetchAlerts()
  } catch {
    // The store exposes the error state to the view.
  }
}

async function acknowledge(id) {
  busyAlertId.value = id
  actionError.value = ''

  try {
    await alertStore.acknowledgeAlert(id)
  } catch (err) {
    actionError.value = err?.message || 'No se pudo reconocer la alerta.'
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
  clientFilter.value = 'ALL'
  stateFilter.value = 'ALL'
  severityFilter.value = 'ALL'
}

function stateLabel(state) {
  const labels = {
    ACTIVE: 'Sin reconocer',
    ACKNOWLEDGED: 'Reconocida',
    RESOLVED: 'Resuelta',
  }

  return labels[state] || state || '—'
}

function severityLabel(severity) {
  const labels = {
    CRITICAL: 'Crítica',
    WARNING: 'Advertencia',
  }

  return labels[severity] || severity || '—'
}

function severityClass(severity) {
  const classes = {
    CRITICAL: 'bg-red-100 text-red-800',
    WARNING: 'bg-amber-100 text-amber-800',
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
})
</script>
