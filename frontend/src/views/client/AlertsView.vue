<!-- Temporary Alertview created for issue 159 before further changes-->
<template>
  <section class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-slate-900">Alertas</h1>
      <p class="mt-1 text-sm text-slate-600">
        Consulta y gestiona las alertas de tus edificios.
      </p>
    </div>

    <LoadingState
      v-if="alertsStore.status === 'loading' || alertsStore.status === 'idle'"
      message="Cargando alertas…"
    />

    <ErrorState
      v-else-if="alertsStore.status === 'error'"
      title="No se han podido cargar las alertas"
      :message="alertsStore.error?.message || alertsStore.error"
      @retry="loadAlerts"
    />

    <EmptyState
      v-else-if="alerts.length === 0"
      title="No hay alertas"
      icon="alert"
    />

    <div v-else class="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50 text-left text-xs uppercase text-slate-500">
          <tr>
            <th class="px-4 py-3">Alerta</th>
            <th class="px-4 py-3">Organización</th>
            <th class="px-4 py-3">Sensor / edificio</th>
            <th class="px-4 py-3">Severidad</th>
            <th class="px-4 py-3">Estado</th>
            <th class="px-4 py-3">Fecha</th>
            <th class="px-4 py-3">Acciones</th>
          </tr>
        </thead>

        <tbody class="divide-y divide-slate-100">
          <AlertRow
            v-for="alert in alerts"
            :key="alert.id"
            :alert="alert"
            :busy="busyAlertId === alert.id"
            @acknowledge="acknowledgeAlert"
            @resolve="resolveAlert"
          />
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAlertsStore } from '../../stores/alerts'
import AlertRow from '../../components/AlertRow.vue'
import LoadingState from '../../components/LoadingState.vue'
import ErrorState from '../../components/ErrorState.vue'
import EmptyState from '../../components/EmptyState.vue'

const alertsStore = useAlertsStore()
const busyAlertId = ref(null)

const alerts = computed(() => alertsStore.alerts)

async function loadAlerts() {
  try {
    await alertsStore.fetchAlerts()
  } catch {
    // El estado de error ya lo gestiona el store.
  }
}

async function acknowledgeAlert(id) {
  busyAlertId.value = id

  try {
    await alertsStore.acknowledgeAlert(id)
  } catch {
    // El store conserva el error para poder mostrarlo.
  } finally {
    busyAlertId.value = null
  }
}

async function resolveAlert(id) {
  busyAlertId.value = id

  try {
    await alertsStore.resolveAlert(id)
  } catch {
    // El store conserva el error para poder mostrarlo.
  } finally {
    busyAlertId.value = null
  }
}

onMounted(loadAlerts)
</script>