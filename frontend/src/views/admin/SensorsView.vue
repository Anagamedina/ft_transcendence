<!--
  ADMIN SENSORS VIEW
  All sensors with counters and a DataTable (search, status and type filters,
  pagination). Status and type texts come from useLabels.
-->

<template>
  <AdminLayout>
    <section class="space-y-6">
      <header class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-slate-900">Sensores</h1>
          <p class="mt-1 text-sm text-slate-500">
            Consulta y filtra los sensores registrados.
          </p>
        </div>

        <button
          type="button"
          class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium hover:bg-slate-50"
          :disabled="status === 'loading'"
          @click="loadSensors"
        >
          Actualizar
        </button>
      </header>

      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div class="rounded-xl border border-slate-200 bg-white p-4">
          <p class="text-sm text-slate-500">Total</p>
          <p class="mt-1 text-2xl font-semibold">{{ sensors.length }}</p>
        </div>
        <div class="rounded-xl border border-slate-200 bg-white p-4">
          <p class="text-sm text-slate-500">Conectados</p>
          <p class="mt-1 text-2xl font-semibold">{{ onlineCount }}</p>
        </div>
        <div class="rounded-xl border border-slate-200 bg-white p-4">
          <p class="text-sm text-slate-500">Sin conexión</p>
          <p class="mt-1 text-2xl font-semibold">{{ offlineCount }}</p>
        </div>
      </div>

      <DataTable
        :columns="COLUMNS"
        :rows="sensors"
        :search-fields="['name', 'location', 'id']"
        search-placeholder="Buscar por nombre o ubicación..."
        :filters="filters"
        :loading="status === 'loading' || status === 'idle'"
        :error="errorMessage"
        item-name="sensores"
        empty-title="No hay sensores registrados"
        empty-message="Cuando haya sensores disponibles, aparecerán aquí."
        icon="droplet"
        caption="Sensores"
        @retry="loadSensors"
      >
        <template #row="{ row: sensor }">
          <tr>
            <td class="whitespace-nowrap px-4 py-3 font-medium text-slate-900">
              {{ sensor.name }}
            </td>
            <td class="px-4 py-3 text-slate-600">
              {{ sensor.location || '—' }}
            </td>
            <td class="px-4 py-3 text-slate-600">
              {{ label('SensorType', sensor.sensor_type) }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-slate-600">
              {{ sensor.min_pressure ?? '—' }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-slate-600">
              {{ sensor.max_pressure ?? '—' }}
            </td>
            <td class="px-4 py-3">
              <StatusPill type="SensorStatus" :value="sensor.status" />
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-slate-600">
              {{ formatDate(sensor.last_seen_at) }}
            </td>
          </tr>
        </template>
      </DataTable>
    </section>
  </AdminLayout>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import AdminLayout from '../../layouts/AdminLayout.vue'
import DataTable from '../../components/DataTable.vue'
import StatusPill from '../../components/StatusPill.vue'
import { useSensorsStore } from '../../stores/sensors.js'
import { useLabels } from '../../composables/useLabels'

const sensorStore = useSensorsStore()
const { label } = useLabels()

const COLUMNS = [
  { key: 'name', label: 'Sensor' },
  { key: 'location', label: 'Ubicación' },
  { key: 'sensor_type', label: 'Tipo' },
  { key: 'min_pressure', label: 'Presión mín.' },
  { key: 'max_pressure', label: 'Presión máx.' },
  { key: 'status', label: 'Estado' },
  { key: 'last_seen_at', label: 'Última conexión' },
]

const sensors = computed(() => sensorStore.sensors)
const status = computed(() => sensorStore.status)
const error = computed(() => sensorStore.error)

const errorMessage = computed(() =>
  status.value === 'error'
    ? error.value?.message || 'Se ha producido un error inesperado.'
    : ''
)

const onlineCount = computed(
  () => sensors.value.filter((sensor) => sensor.status === 'ONLINE').length
)

const offlineCount = computed(
  () => sensors.value.filter((sensor) => sensor.status === 'OFFLINE').length
)

// Type options are built from the loaded sensors, so only existing types appear
const filters = computed(() => [
  {
    key: 'status',
    label: 'Estado',
    allLabel: 'Todos los estados',
    options: ['ONLINE', 'OFFLINE'].map((value) => ({
      value,
      label: label('SensorStatus', value),
    })),
  },
  {
    key: 'sensor_type',
    label: 'Tipo',
    allLabel: 'Todos los tipos',
    options: [...new Set(sensors.value.map((sensor) => sensor.sensor_type).filter(Boolean))].map(
      (value) => ({ value, label: label('SensorType', value) })
    ),
  },
])

async function loadSensors() {
  try {
    await sensorStore.fetchSensors()
  } catch {
    // The store exposes the error state to the view.
  }
}

// Short Spanish date and time, e.g. "8/9/26, 10:30"
const dateFormat = new Intl.DateTimeFormat('es-ES', { dateStyle: 'short', timeStyle: 'short' })

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '—' : dateFormat.format(date)
}

onMounted(loadSensors)
</script>