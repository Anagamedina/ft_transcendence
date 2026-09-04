<template>
  <MainLayout header-title="AquaGuard" sidebar-app-name="AquaGuard">
    <div v-if="sensor" class="max-w-md">
      <div
        class="bg-white border-2 rounded-xl shadow-lg p-6"
        :class="status.borderClass"
      >
        <div class="flex justify-between items-start gap-2 mb-2">
          <div class="min-w-0">
            <h2 class="text-2xl font-bold text-gray-900">{{ sensor.name }}</h2>
            <p class="text-sm text-gray-500">{{ sensor.location }}</p>
          </div>
          <span
            class="shrink-0 inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-semibold"
            :class="[status.bgClass, status.textClass]"
          >
            {{ status.icon }} {{ status.label }}
          </span>
        </div>

        <div class="mt-6">
          <p v-if="hasReading" class="text-4xl font-bold text-aqua-900">
            {{ sensor.value }}
            <span class="text-lg font-medium text-gray-500">{{
              sensor.unit
            }}</span>
          </p>
          <p v-else class="text-xl font-medium text-gray-400">
            — sin lectura —
          </p>
        </div>
      </div>

      <router-link
        to="/test"
        class="inline-block mt-4 text-aqua-600 hover:underline"
      >
        &larr; Volver
      </router-link>
    </div>

    <div v-else class="text-gray-500">
      Sensor no encontrado.
      <router-link to="/test" class="text-aqua-600 hover:underline"
        >Volver</router-link
      >
    </div>
  </MainLayout>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import MainLayout from "../../layouts/MainLayout.vue";
import { useSensorsStore } from "../../stores/sensors";
import { useSensorStatus } from "../../composables/useSensorStatus";

const route = useRoute();
const sensorsStore = useSensorsStore();

const sensor = computed(() =>
  sensorsStore.sensors.find((s) => String(s.id) === route.params.id),
);

const status = computed(() => useSensorStatus(sensor.value?.statusKey));
const hasReading = computed(
  () =>
    sensor.value?.value !== null &&
    sensor.value?.value !== undefined &&
    sensor.value?.value !== "",
);
</script>
