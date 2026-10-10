<template>
  <MainLayout
    header-title="AquaGuard Frontend — Issue #4"
    sidebar-app-name="AquaGuard Test"
  >
    <div class="space-y-6">
      <!-- Bloque de depuración: solo para desarrollo, confirma que los stores de Pinia están conectados -->
      <div class="p-4 bg-gray-100 rounded-lg text-sm">
        <p class="font-semibold text-gray-500 mb-1">
          [DEV] Estado de los stores
        </p>
        <p>Usuario: {{ authStore.user }}</p>
        <p>Sensores en el store: {{ sensorsStore.sensorCount }}</p>
        <p>Alertas: {{ alertsStore.alerts }}</p>
      </div>

      <div
        v-if="sensorsStore.sensors.length"
        class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
      >
        <router-link
          v-for="sensor in sensorsStore.sensors"
          :key="sensor.id"
          :to="`/sensors/${sensor.id}`"
          class="block h-full hover:opacity-90 transition"
        >
          <SensorCard
            :name="sensor.name"
            :location="sensor.location"
            :statusKey="sensor.statusKey"
            :value="sensor.value"
            :unit="sensor.unit"
          />
        </router-link>
      </div>
      <p v-else class="text-gray-500">No hay sensores disponibles.</p>

      <button
        @click="modalAbierto = true"
        class="border-2 border-aqua-600 text-aqua-600 px-4 py-2 rounded-lg hover:bg-aqua-50 transition"
      >
        Abrir modal
      </button>
    </div>

    <Modal
      :show="modalAbierto"
      title="Prueba de Modal"
      @close="modalAbierto = false"
    >
      <p>Este es el contenido de prueba del modal.</p>

      <template #footer>
        <button
          @click="modalAbierto = false"
          class="px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-50 transition"
        >
          Cancelar
        </button>
        <button
          @click="modalAbierto = false"
          class="px-4 py-2 rounded-lg bg-aqua-600 text-white hover:bg-aqua-800 transition"
        >
          Confirmar
        </button>
      </template>
    </Modal>
  </MainLayout>
</template>

<script setup>
import { ref } from "vue";
import MainLayout from "../../layouts/MainLayout.vue";
import Modal from "../../components/Modal.vue";
import SensorCard from "../../components/SensorCard.vue";
import { useAuthStore } from "../../stores/auth";
import { useSensorsStore } from "../../stores/sensors";
import { useAlertsStore } from "../../stores/alerts";

const authStore = useAuthStore();
const sensorsStore = useSensorsStore();
sensorsStore.sensors = [
  {
    id: 1,
    name: "Sensor Cocina",
    location: "Planta baja",
    statusKey: "normal",
    value: 2.3,
    unit: "bar",
  },
  {
    id: 2,
    name: "Sensor Baño 2",
    location: "Planta 1",
    statusKey: "warning",
    value: 4.8,
    unit: "bar",
  },
  {
    id: 3,
    name: "Sensor Terraza",
    location: "Ático",
    statusKey: "critical",
    value: 0.4,
    unit: "bar",
  },
  { id: 4, name: "Sensor Sótano", location: "Planta -1", statusKey: "offline" },
];

const alertsStore = useAlertsStore();

const modalAbierto = ref(false);
</script>
