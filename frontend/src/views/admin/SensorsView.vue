<!--

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
        <p class="text-sm text-slate-500">En línea</p>
        <p class="mt-1 text-2xl font-semibold">{{ onlineCount }}</p>
      </div>
      <div class="rounded-xl border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Fuera de línea</p>
        <p class="mt-1 text-2xl font-semibold">{{ offlineCount }}</p>
      </div>
    </div>

    <div class="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 md:flex-row">
      <input
        v-model.trim="search"
        type="search"
        placeholder="Buscar por nombre o ubicación..."
        aria-label="Buscar sensores"
        class="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
      />

      <select
        v-model="statusFilter"
        aria-label="Filtrar por estado"
        class="rounded-lg border border-slate-300 px-3 py-2 text-sm"
      >
        <option value="ALL">Todos los estados</option>
        <option value="ONLINE">En línea</option>
        <option value="OFFLINE">Fuera de línea</option>
      </select>

      <select
        v-model="typeFilter"
        aria-label="Filtrar por tipo"
        class="rounded-lg border border-slate-300 px-3 py-2 text-sm"
      >
        <option value="ALL">Todos los tipos</option>
        <option
          v-for="type in sensorTypes"
          :key="type"
          :value="type"
        >
          {{ type }}
        </option>
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
      v-if="status === 'loading' || status === 'idle'"
      class="rounded-xl border border-slate-200 bg-white p-10 text-center text-slate-600"
      role="status"
    >
      Cargando sensores...
    </div>

    <div
      v-else-if="status === 'error'"
      class="rounded-xl border border-red-200 bg-white p-6"
      role="alert"
    >
      <h2 class="font-semibold text-red-700">No se pudieron cargar los sensores</h2>
      <p class="mt-2 text-sm text-slate-600">
        {{ error?.message || 'Se ha producido un error inesperado.' }}
      </p>
      <button
        type="button"
        class="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
        @click="loadSensors"
      >
        Reintentar
      </button>
    </div>

    <div
      v-else-if="sensors.length === 0"
      class="rounded-xl border border-slate-200 bg-white p-10 text-center"
    >
      <h2 class="font-semibold text-slate-800">No hay sensores registrados</h2>
      <p class="mt-2 text-sm text-slate-500">
        Cuando haya sensores disponibles, aparecerán aquí.
      </p>
    </div>

    <div
      v-else-if="filteredSensors.length === 0"
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
            <th scope="col" class="px-4 py-3 font-medium">Sensor</th>
            <th scope="col" class="px-4 py-3 font-medium">Ubicación</th>
            <th scope="col" class="px-4 py-3 font-medium">Tipo</th>
            <th scope="col" class="px-4 py-3 font-medium">Presión mín.</th>
            <th scope="col" class="px-4 py-3 font-medium">Presión máx.</th>
            <th scope="col" class="px-4 py-3 font-medium">Estado</th>
            <th scope="col" class="px-4 py-3 font-medium">Última conexión</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="sensor in filteredSensors" :key="sensor.id">
            <td class="whitespace-nowrap px-4 py-3 font-medium text-slate-900">
              {{ sensor.name }}
            </td>
            <td class="px-4 py-3 text-slate-600">
              {{ sensor.location || '—' }}
            </td>
            <td class="px-4 py-3 text-slate-600">
              {{ sensor.sensor_type || '—' }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-slate-600">
              {{ sensor.min_pressure ?? '—' }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-slate-600">
              {{ sensor.max_pressure ?? '—' }}
            </td>
            <td class="whitespace-nowrap px-4 py-3">
              <span
                class="rounded-full px-2.5 py-1 text-xs font-medium"
                :class="sensor.status === 'ONLINE'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-slate-100 text-slate-700'"
              >
                {{ sensor.status === 'ONLINE' ? 'En línea' : 'Fuera de línea' }}
              </span>
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-slate-600">
              {{ formatDate(sensor.last_seen_at) }}
            </td>
          </tr>
        </tbody>
      </table>

      <p class="border-t border-slate-100 px-4 py-3 text-sm text-slate-500">
        {{ filteredSensors.length }} de {{ sensors.length }} sensores
      </p>
    </div>
  </section>
  </AdminLayout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import AdminLayout from '../../layouts/AdminLayout.vue'
import { useSensorsStore } from '../../stores/sensors.js'

const sensorStore = useSensorsStore()

const search = ref('')
const statusFilter = ref('ALL')
const typeFilter = ref('ALL')

const sensors = computed(() => sensorStore.sensors)
const status = computed(() => sensorStore.status)
const error = computed(() => sensorStore.error)

const onlineCount = computed(
  () => sensors.value.filter((sensor) => sensor.status === 'ONLINE').length
)

const offlineCount = computed(
  () => sensors.value.filter((sensor) => sensor.status === 'OFFLINE').length
)

const sensorTypes = computed(() => [
  ...new Set(
    sensors.value
      .map((sensor) => sensor.sensor_type)
      .filter(Boolean)
  ),
])

const filteredSensors = computed(() => {
  const query = search.value.toLocaleLowerCase()

  return sensors.value.filter((sensor) => {
    const matchesSearch = [
      sensor.name,
      sensor.location,
      sensor.id,
    ].some((value) =>
      String(value ?? '').toLocaleLowerCase().includes(query)
    )

    const matchesStatus =
      statusFilter.value === 'ALL' ||
      sensor.status === statusFilter.value

    const matchesType =
      typeFilter.value === 'ALL' ||
      sensor.sensor_type === typeFilter.value

    return matchesSearch && matchesStatus && matchesType
  })
})

async function loadSensors() {
  try {
    await sensorStore.fetchSensors()
  } catch {
    // The store exposes the error state to the view.
  }
}

function resetFilters() {
  search.value = ''
  statusFilter.value = 'ALL'
  typeFilter.value = 'ALL'
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

onMounted(loadSensors)
</script>
