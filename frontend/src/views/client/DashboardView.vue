<!-- CLIENT DASHBOARD — sensores propios, alertas. -->

<template>
  <div class="mx-auto max-w-7xl space-y-8">
    <header>
      <h1 class="text-3xl font-bold text-gray-900">
        Panel de control
      </h1>
      <p class="mt-2 text-sm text-gray-600">
        Estado de los sensores y alertas de tu organización.
      </p>
    </header>

    <!-- Auth / organization -->
    <section
      v-if="!authStore.user?.organization_id"
      class="rounded-xl border border-amber-200 bg-amber-50 p-5"
      role="status"
    >
      <h2 class="font-semibold text-amber-900">
        Organización no disponible
      </h2>
      <p class="mt-1 text-sm text-amber-800">
        Tu perfil no está asociado a una organización.
        Contacta con el administrador.
      </p>
    </section>

    <template v-else>
      <!-- Independent loading/error states -->
      <section>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <KPICard
            label="Sensores"
            :value="sensorStore.status === 'success'
              ? sensorStore.sensorCount
              : '—'"
          >
            <template #icon>
              <AppIcon name="droplet" />
            </template>
          </KPICard>

          <KPICard
            label="Alertas activas"
            :value="alertsStore.status === 'success'
              ? activeAlertCount
              : '—'"
          >
            <template #icon>
              <AppIcon name="alert" />
            </template>
          </KPICard>
        </div>
      </section>

      <section id="sensors">
        <SensorsSummary
          :sensors="sensorStore.sensors"
          :status="sensorStore.status"
          :error="sensorStore.error"
          @retry="retrySensors"
        />
      </section>

      <section id="alerts">
        <AlertsSummary
          :alerts="activeAlerts"
          :status="alertsStore.status"
          :error="alertsStore.error"
          @retry="loadAlerts"
        />
      </section>

      <!-- Reading history -->
      <section id="history" class="rounded-xl border border-gray-200 bg-white p-5 shadow-md">
        <h2 class="mb-4 text-lg font-bold text-gray-800">
          Histórico de lecturas
        </h2>

        <LoadingState
          v-if="historyStatus === 'loading'"
          message="Cargando histórico…"
          compact
        />

        <ErrorState
          v-else-if="historyStatus === 'error'"
          title="No se ha podido cargar el histórico"
          :message="historyError"
          @retry="retryHistory"
          compact
        />

        <EmptyState
          v-else-if="historyStatus === 'empty'"
          title="No hay lecturas disponibles"
          message="Las lecturas aparecerán aquí cuando tus sensores registren datos."
          icon="bar-chart"
          compact
        />

        <div v-else-if="historyStatus === 'success'" class="overflow-x-auto">
          <div
            v-if="historyWarning"
            class="mb-3 flex items-center justify-between gap-3 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800"
            role="status"
          >
            <span>{{ historyWarning }}</span>
            <button
              type="button"
              class="shrink-0 rounded-lg border border-amber-300 px-3 py-1 font-medium hover:bg-amber-100"
              @click="loadHistory"
            >
              Reintentar
            </button>
          </div>
          <table class="w-full text-left text-sm">
            <thead>
              <tr class="border-b border-gray-200 text-gray-500">
                <th class="px-3 py-3">Sensor</th>
                <th class="px-3 py-3">Presión</th>
                <th class="px-3 py-3">Fecha</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="reading in history"
                :key="reading.id"
                class="border-b border-gray-100"
              >
                <td class="px-3 py-3">
                  {{ sensorName(reading.sensor_id) }}
                </td>
                <td class="px-3 py-3">
                  {{ formatPressure(reading) }}
                </td>
                <td class="px-3 py-3">
                  {{ formatDate(reading.measured_at) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <p v-else class="text-sm text-gray-500">
          Selecciona un sensor para consultar su histórico.
        </p>
      </section>

      <!-- Profile -->
      <section id="profile" class="rounded-xl border border-gray-200 bg-white p-5 shadow-md">
        <h2 class="mb-4 text-lg font-bold text-gray-800">
          Mi perfil
        </h2>

        <dl class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <dt class="text-sm text-gray-500">Nombre</dt>
            <dd class="font-medium text-gray-900">
              {{ authStore.user?.name || 'No disponible' }}
            </dd>
          </div>
          <div>
            <dt class="text-sm text-gray-500">Correo electrónico</dt>
            <dd class="font-medium text-gray-900">
              {{ authStore.user?.email || 'No disponible' }}
            </dd>
          </div>
          <div v-if="organizationName">
            <dt class="text-sm text-gray-500">Organización</dt>
            <dd class="font-medium text-gray-900">
              {{ organizationName }}
            </dd>
          </div>
        </dl>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'

import { useAuthStore } from '../../stores/auth'
import { useSensorsStore } from '../../stores/sensors'
import { useAlertsStore } from '../../stores/alerts'
import readingService from '../../services/reading.service.js'

import AppIcon from '../../components/AppIcon.vue'
import KPICard from '../../components/KPICard.vue'
import SensorsSummary from '../../components/SensorsSummary.vue'
import AlertsSummary from '../../components/AlertsSummary.vue'
import LoadingState from '../../components/LoadingState.vue'
import ErrorState from '../../components/ErrorState.vue'
import EmptyState from '../../components/EmptyState.vue'

const authStore = useAuthStore()
const sensorStore = useSensorsStore()
const alertsStore = useAlertsStore()

const history = ref([])
const historyStatus = ref('idle')
const historyError = ref(null)
const historyWarning = ref(null)

let cancelled = false

const activeAlerts = computed(() =>
  alertsStore.alerts.filter(
    alert => alert.status !== 'RESOLVED'
  )
)

const activeAlertCount = computed(() => activeAlerts.value.length)

// The profile only has organization_id; the sensors carry the organization name
const organizationName = computed(() =>
  sensorStore.sensors.find(sensor => sensor.organization_name)?.organization_name
    || null
)

function findSensor(sensorId) {
  return sensorStore.sensors.find(sensor => sensor.id === sensorId)
}

function sensorName(sensorId) {
  return findSensor(sensorId)?.name || 'Sensor'
}

// Spanish number format: '6,8 bar'
const pressureFormat = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 2 })

function formatPressure(reading) {
  const unit = findSensor(reading.sensor_id)?.unit || 'bar'
  return `${pressureFormat.format(reading.pressure)} ${unit}`
}

function formatDate(value) {
  if (!value) return '—'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'

  return date.toLocaleString('es-ES')
}

async function loadSensors() {
  try {
    await sensorStore.fetchSensors()
  } catch {
    // The store exposes the error state to SensorsSummary.
  }
}

// The history depends on the sensor list, so it is reloaded with it.
async function retrySensors() {
  await loadSensors()
  await loadHistory()
}

// If the sensors failed, fetch them again before the history.
async function retryHistory() {
  if (sensorStore.status === 'error') {
    await retrySensors()
    return
  }
  await loadHistory()
}

async function loadAlerts() {
  try {
    await alertsStore.fetchAlerts()
  } catch {
    // The store exposes the error state to AlertsSummary.
  }
}

async function loadHistory() {
  historyWarning.value = null

  if (cancelled) return

  history.value = []
  historyError.value = null

  if (sensorStore.status !== 'success') {
    historyStatus.value =
      sensorStore.status === 'error' ? 'error' : 'idle'

    historyError.value =
      sensorStore.status === 'error'
        ? 'No se pueden consultar las lecturas porque no se han podido cargar los sensores.'
        : null

    return
  }

  const sensorIds = sensorStore.sensors.map(sensor => sensor.id)

  if (!sensorIds.length) {
    historyStatus.value = 'empty'
    return
  }

  historyStatus.value = 'loading'

  // Each sensor is loaded independently.
  const results = await Promise.allSettled(
    sensorIds.map(sensorId =>
      readingService.getSensorReadings(sensorId)
    )
  )

  if (cancelled) return

  const successful = results
    .filter(result => result.status === 'fulfilled')
    .flatMap(result => result.value.data.items || [])
    .sort(
      (a, b) =>
        new Date(b.measured_at) - new Date(a.measured_at)
    )

  const failedCount = results.filter(
    result => result.status === 'rejected'
  ).length

  history.value = successful

  // Every sensor failed.
  if (failedCount === results.length) {
    historyStatus.value = 'error'
    historyError.value =
      'No se pudo cargar el histórico de ningún sensor.'
    return
  }

  if (failedCount > 0) {
    historyStatus.value = successful.length ? 'success' : 'error'

    historyWarning.value =
      `${failedCount} sensor(es) no han podido proporcionar su historial.`

    if (!successful.length) {
      historyError.value =
        'No se ha podido recuperar ninguna lectura.'
    }

    return
  }

  historyStatus.value =
    successful.length ? 'success' : 'empty'
}
onMounted(async () => {
  await Promise.all([loadSensors(), loadAlerts()])

  if (!cancelled) {
    await loadHistory()
  }
})

onBeforeUnmount(() => {
  cancelled = true
})
</script>
