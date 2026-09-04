<template>
  <div
    class="bg-white border-2 rounded-xl shadow-lg p-6 transition max-w-sm"
    :class="status.borderClass"
  >
    <div class="flex justify-between items-start gap-2 mb-2">
      <div class="min-w-0">
        <h3 class="text-lg font-bold text-gray-900 truncate">{{ name }}</h3>
        <p class="text-sm text-gray-500 truncate">{{ location }}</p>
      </div>
      <span
        class="shrink-0 inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold"
        :class="[status.bgClass, status.textClass]"
      >
        {{ status.icon }} {{ status.label }}
      </span>
    </div>

    <div class="mt-4">
      <p v-if="hasReading" class="text-3xl font-bold text-aqua-900">
        {{ value }}
        <span class="text-base font-medium text-gray-500">{{ unit }}</span>
      </p>
      <p v-else class="text-lg font-medium text-gray-400">— sin lectura —</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useSensorStatus } from "../composables/useSensorStatus";

const props = defineProps({
  name: { type: String, required: true },
  location: { type: String, default: "" },
  // 'normal' | 'warning' | 'critical' | 'offline' — llega ya calculado, este
  // componente solo lo traduce visualmente, no decide umbrales.
  statusKey: { type: String, default: "offline" },
  value: { type: [Number, String], default: null },
  unit: { type: String, default: "bar" },
});

const status = computed(() => useSensorStatus(props.statusKey));
const hasReading = computed(
  () => props.value !== null && props.value !== undefined && props.value !== "",
);
</script>
