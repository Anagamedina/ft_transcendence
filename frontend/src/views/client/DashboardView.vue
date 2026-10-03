<!-- CLIENT DASHBOARD — sensores propios, histórico Chart.js, alertas. -->

<template>
  <div class="min-h-screen bg-gray-100 p-6">
    <div class="max-w-7xl mx-auto">

      <h1 class="text-3xl font-bold text-gray-900 mb-6">
        Dashboard
      </h1>
          <div>
      <button
        type="button"
        @click="handleLogout"
        :disabled="authStore.status === 'loading'"
      >
        {{ authStore.status === 'loading'
          ? 'Login out...'
          : 'Logout'
        }}
      </button>
    </div>

      <div v-if="sensorStore.status === 'loading'">
        Loading sensor......
      </div>

      <div v-else-if="sensorStore.error">
       Sensor loading failed.
      </div>

      <div v-else>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

          <div
            v-for="sensor in sensorStore.sensors"
            :key="sensor.id"
            class="bg-white rounded-xl shadow p-6"
          >
            <h2 class="text-xl font-semibold text-gray-900">
              {{ sensor.name }}
            </h2>

            <p class="text-gray-600 mt-2">
              Pressure :
              {{ sensor.current_pressure ?? "--" }} bar
            </p>

            <p class="text-gray-500 text-sm mt-2">
              Status : {{ sensor.status }}
            </p>
          </div>

      <div class="mt-8">
        <h2 class="text-2xl font-bold text-gray-900 mb-4">
          Alerts
        </h2>

        <div v-if="alertsStore.status === 'loading'">
          Loading Alert...
        </div>

        <div v-else-if="alertsStore.error">
          Alert loading failed.
        </div>

        <div v-else-if="alertsStore.alerts.length === 0">
          No Alerts.
        </div>

        <div v-else class="space-y-4">
      <div
        v-for="alert in alertsStore.alerts"
        :key="alert.id"
        class="bg-white rounded-xl shadow p-4">

        <h3 class="font-semibold text-gray-900">
          {{ alert.message }}
        </h3>

        <p class="text-sm text-gray-500 mt-1">
          Statut : {{ alert.status }}
        </p>

        <div class="flex gap-3 mt-4">

          <button
            v-if="!alert.acknowledged_at"
            type="button"
            @click="alertsStore.acknowledgeAlert(alert.id)"
            class="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600"
          >
            Acknowledge
          </button>

          <button
            v-if="alert.status !== 'RESOLVED'"
            type="button"
            @click="alertsStore.resolveAlert(alert.id)"
            class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            Resolve
          </button>

        </div>
      </div>
    </div>
      </div>
        </div>
      </div>

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
  await sensorStore.fetchSensors();
  await alertsStore.fetchAlerts();
});

</script>