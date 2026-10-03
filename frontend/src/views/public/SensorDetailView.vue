<template>
  <MainLayout header-title="AquaGuard" sidebar-app-name="AquaGuard">
    <!--
      This file is the "integration layer": it is the only place that knows
      about the store. SensorDetail.vue (the pure component) only receives
      props. When Lylia wires up the real API, this is the only file that
      should need to change.
    -->
     <div v-if="sensorsStore.status === 'loading'">
      Loading sensor...
    </div>

    <div v-else-if="sensorsStore.status === 'error'">
      An error occurred while loading the sensors
    </div>

    <div v-else-if="!sensor">
      Sensor not found
    </div>

    <div v-else-if="readingsStore.status === 'loading'">
      Loading readings...
    </div>

    <div v-else-if="readingsStore.status === 'error'">
      An error occurred while loading the readings
    </div>

    <SensorDetail
      v-else
      :sensor="sensorForView"
    />

    <router-link
      to="/test"
      class="inline-block mt-4 text-aqua-600 hover:underline"
    >
      &larr; Volver
    </router-link>
  </MainLayout>
</template>

<script setup>
import { computed, onMounted} from 'vue'
import { useRoute } from 'vue-router'
import MainLayout from '../../layouts/MainLayout.vue'
import SensorDetail from '../../components/SensorDetail.vue'

import { useSensorsStore } from '../../stores/sensors'
import { useReadingsStore } from '../../stores/readings'

const route = useRoute()

const sensorsStore = useSensorsStore()
const readingsStore = useReadingsStore()

const sensor = computed(() =>
  sensorsStore.sensors.find((s) => String(s.id) === String(route.params.id))
)

const latestReading = computed(() => {
  if (readingsStore.readings.length === 0) {
    return null;
  }
  return [...readingsStore.readings].sort(
    (a, b) =>
      new Date(b.measured_at) - new Date(a.measured_at)
  )[0];
});

const sensorForView = computed(() => {
  if (!sensor.value) {
    return null;
  }
  return {
    ...sensor.value,
    value: latestReading.value?.pressure ?? null,
    unit: "bar",
  };
});

onMounted(async () => {
  if (sensorsStore.sensors.length === 0) {
    await sensorsStore.fetchSensors();
  }
  if (sensor.value) {
    sensorsStore.selectSensor(sensor.value);

    await readingsStore.fetchReadings(sensor.value.id);
  }
});

</script>
