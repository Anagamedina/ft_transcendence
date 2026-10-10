<!-- CLIENT DASHBOARD — sensores propios, alertas. -->

<template>
  <div class="min-h-screen bg-gray-100 p-6">
    <div class="max-w-7xl mx-auto">

      <!-- Header -->
      <h1 class="text-3xl font-bold text-gray-900 mb-6">
        Panel de control
      </h1>

      <!-- Logout -->
      <div>
        <button
          type="button"
          @click="handleLogout"
          :disabled="authStore.status === 'loading'"
          class="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{
            authStore.status === 'loading'
              ? 'Cerrando sesión...'
              : 'Cerrar sesión'
          }}
        </button>
      </div>

      <!-- ==================== SENSORS ==================== -->

      <section class="mt-8">

        <h2 class="text-2xl font-bold text-gray-900 mb-4">
          Sensores
        </h2>

        <div v-if="sensorStore.status === 'loading'">
          Cargando sensores...
        </div>

        <div v-else-if="sensorStore.error">
          Error al cargar los sensores.
        </div>

        <div v-else-if="sensorStore.sensors.length === 0">
          No hay sensores.
        </div>

        <div
          v-else
          class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >

          <div
            v-for="sensor in sensorStore.sensors"
            :key="sensor.id"
            class="bg-white rounded-xl shadow p-6"
          >

            <h3 class="text-xl font-semibold text-gray-900">
              {{ sensor.name }}
            </h3>

            <p class="text-gray-500 text-sm mt-2">
              Estado: {{ sensor.status }}
            </p>

          </div>

        </div>

      </section>

      <!-- ==================== ALERTS ==================== -->

      <section class="mt-8">

        <h2 class="text-2xl font-bold text-gray-900 mb-4">
          Alertas
        </h2>

        <div v-if="alertsStore.status === 'loading'">
          Cargando alertas...
        </div>

        <div v-else-if="alertsStore.error">
          Error al cargar las alertas.
        </div>

        <div v-else-if="alertsStore.alerts.length === 0">
          No hay alertas.
        </div>

        <div v-else class="space-y-4">

          <div
            v-for="alert in alertsStore.alerts"
            :key="alert.id"
            class="bg-white rounded-xl shadow p-4"
          >

            <h3 class="font-semibold text-gray-900">
              {{ alert.message }}
            </h3>

            <p class="text-sm text-gray-500 mt-1">
              Estado: {{ alert.status }}
            </p>

            <!-- Alert actions -->
            <div class="flex gap-3 mt-4">

              <!-- Acknowledge -->
              <button
                v-if="!alert.acknowledged_at && alert.status !== 'RESOLVED'"
                type="button"
                @click="alertsStore.acknowledgeAlert(alert.id)"
                class="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600"
              >
                Acusar recibo
              </button>

              <!-- Resolve -->
              <button
                v-if="alert.status !== 'RESOLVED'"
                type="button"
                @click="alertsStore.resolveAlert(alert.id)"
                class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Resolver
              </button>

            </div>

          </div>

        </div>

      </section>

    </div>
  </div>
</template>


<script setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";

import { useAuthStore } from "../../stores/auth";
import { useSensorsStore } from "../../stores/sensors";
import { useAlertsStore } from "../../stores/alerts";

const router = useRouter();

const authStore = useAuthStore();
const sensorStore = useSensorsStore();
const alertsStore = useAlertsStore();


async function handleLogout() {
  await authStore.logout();

  router.push("/login");
}


onMounted(async () => {

  // charging both resources separetly so if sensors fail, alerts can still be loaded
  try {
    await sensorStore.fetchSensors();
  } catch (error) {
    console.error("Error cargando sensores:", error);
  }

  try {
    await alertsStore.fetchAlerts();
  } catch (error) {
    console.error("Error cargando alertas:", error);
  }

});
</script>