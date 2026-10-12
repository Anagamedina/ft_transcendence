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

      <!-- Issue #160 (F4 + F5): building floor by floor and pressure chart, mock data -->
      <div class="grid grid-cols-1 items-start gap-5 lg:grid-cols-[420px_minmax(0,1fr)]">
        <BuildingStack
          :name="demoBuilding.name"
          :floors="demoBuilding.floors"
          :basements="demoBuilding.basements"
          :sensors="demoSensors"
          :selected-id="selectedSensorId"
          @select="selectedSensorId = $event"
        />
        <SensorDetailPanel
          :sensor="selectedSensor"
          :readings="selectedReadings"
          :alert-count="demoAlertCounts[selectedSensorId] ?? 0"
        />
      </div>

      <!-- Empty state: building without sensors -->
      <BuildingStack name="Edificio sin sensores" :floors="3" :basements="1" :sensors="[]" />
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
import { ref, computed } from "vue";
import MainLayout from "../../layouts/MainLayout.vue";
import BuildingStack from "../../components/BuildingStack.vue";
import SensorDetailPanel from "../../components/SensorDetailPanel.vue";
import { demoBuilding, demoSensors, demoReadings, demoAlertCounts } from "../../services/fixtures/building";
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

// Issue #160 demo: selected sensor and its mock readings.
// As in the mockup, the panel always shows a sensor: the worst one first.
const healthRank = { CRITICAL: 0, WARNING: 1, OFFLINE: 2, OK: 3 };
const selectedSensorId = ref(
  [...demoSensors].sort((a, b) => healthRank[a.health] - healthRank[b.health])[0].id,
);
const selectedSensor = computed(
  () => demoSensors.find((s) => s.id === selectedSensorId.value) || null,
);
const selectedReadings = computed(() => demoReadings(selectedSensor.value));
</script>
