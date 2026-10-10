<template>
  <div v-if="sensor" class="max-w-md">
    <div
      class="bg-white border-2 rounded-xl shadow-lg p-6"
      :class="status.borderClass"
    >
      <div
        class="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-2 mb-2"
      >
        <div class="min-w-0 min-h-[3.5rem]">
          <h2 class="text-2xl font-bold text-gray-900 break-words line-clamp-2">
            {{ sensor.name }}
          </h2>
          <p class="text-sm text-gray-500 break-words">{{ sensor.location }}</p>
        </div>
        <span
          class="self-start shrink-0 inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-semibold"
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
        <p v-else class="text-xl font-medium text-gray-400">— sin lectura —</p>
      </div>
    </div>
  </div>

  <div v-else class="text-gray-500">Sensor no encontrado.</div>
</template>

<script setup>
import { computed } from "vue";
import { useSensorStatus } from "../composables/useSensorStatus";

// Pure component: only receives an already-resolved sensor. It has no idea
// whether the data came from a mock, Pinia, or a real API — same principle
// as SensorCard.vue.
const props = defineProps({
  sensor: {
    type: Object,
    default: null,
  },
});

const status = computed(() => useSensorStatus(props.sensor?.statusKey));
const hasReading = computed(
  () =>
    props.sensor?.value !== null &&
    props.sensor?.value !== undefined &&
    props.sensor?.value !== "",
);
</script>
