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
        Chargement des capteurs...
      </div>

      <div v-else-if="sensorStore.error">
        Erreur lors du chargement des capteurs.
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
              Pression :
              {{ sensor.current_pressure ?? "--" }} bar
            </p>

            <p class="text-gray-500 text-sm mt-2">
              Statut : {{ sensor.status }}
            </p>
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
});
</script>