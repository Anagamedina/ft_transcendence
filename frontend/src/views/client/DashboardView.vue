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
          @retry="loadSensors"
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
          @retry="loadHistory"
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
          <p
            v-if="historyWarning"
            class="mt-3 text-sm text-amber-700"
            role="status"
            >
            {{ historyWarning }}
          </p>
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
                  {{ reading.pressure }} bar
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
          <div>
            <dt class="text-sm text-gray-500">Organización</dt>
            <dd class="font-medium text-gray-900">
              {{ authStore.user?.organization_id }}
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

function sensorName(sensorId) {
  return sensorStore.sensors.find(sensor => sensor.id === sensorId)?.name
    || 'Sensor'
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

  // Chaque capteur est chargé indépendamment.
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

  // Tous les capteurs ont échoué.
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
