<template>
  <div
    class="bg-white border-2 rounded-xl shadow-lg p-6 transition h-full flex flex-col"
    :class="borderClass"
  >
    <div
      class="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-2 mb-2"
    >
      <div class="min-w-0">
        <h3
          class="text-lg font-bold text-gray-900 line-clamp-2 break-words"
          :title="name"
        >
          {{ name }}
        </h3>
        <p class="text-sm text-gray-500 truncate" :title="location">
          {{ location }}
        </p>
      </div>
      <StatusPill type="SensorHealth" :value="health" class="self-start shrink-0" />
    </div>

    <div class="mt-auto pt-4">
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
import StatusPill from "./StatusPill.vue";
import { useLabels } from "../composables/useLabels";

const props = defineProps({
  name: { type: String, required: true },
  location: { type: String, default: "" },
  // SensorHealth value (OK | WARNING | CRITICAL | OFFLINE). Old mock keys
  // (normal | warning | critical | offline) are still accepted. It arrives
  // already computed: this component only shows it, it never decides thresholds.
  statusKey: { type: String, default: "OFFLINE" },
  value: { type: [Number, String], default: null },
  unit: { type: String, default: "bar" },
});

const { tone, toneClasses, toSensorHealth } = useLabels();

const health = computed(() => toSensorHealth(props.statusKey));
const borderClass = computed(
  () => toneClasses(tone("SensorHealth", health.value)).border,
);
const hasReading = computed(
  () => props.value !== null && props.value !== undefined && props.value !== "",
);
</script>