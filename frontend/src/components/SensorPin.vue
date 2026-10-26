<!--
  SENSOR PIN
  One sensor inside a floor of BuildingStack (F4), as in the C-Edificio mockup:
  coloured dot (health) + sensor name. Clicking it emits "select" with the
  sensor id so the parent shows that sensor in SensorDetailPanel.
  It only shows data: health arrives already computed by the backend (B3).
  Usage:
    <SensorPin :sensor="sensor" :selected="sensor.id === selectedId" @select="selectedId = $event" />
-->

<template>
  <button
    type="button"
    class="inline-flex min-h-8 max-w-full items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs transition focus:outline-none focus-visible:ring-2 focus-visible:ring-aqua-600 focus-visible:ring-offset-1"
    :class="
      selected
        ? 'border-2 border-aqua-600 bg-aqua-100 text-aqua-900'
        : 'border border-slate-200 bg-white text-slate-700 hover:border-aqua-400'
    "
    :aria-pressed="selected"
    :aria-label="ariaLabel"
    @click="$emit('select', sensor.id)"
  >
    <!-- Offline: wifi-off icon instead of the grey dot (not only colour) -->
    <span
      v-if="health === 'OFFLINE'"
      class="h-3.5 w-3.5 shrink-0 text-slate-600"
      aria-hidden="true"
      ><AppIcon name="wifi-off"
    /></span>
    <span
      v-else
      class="h-[9px] w-[9px] shrink-0 rounded-full"
      :class="dotClass"
      aria-hidden="true"
    ></span>
    <span class="truncate">{{ sensor.name }}</span>
  </button>
</template>

<script setup>
import { computed } from "vue";
import AppIcon from "./AppIcon.vue";
import { useLabels } from "../composables/useLabels";

const props = defineProps({
  // SensorResponse (B3): id, name, health, last_value, unit
  sensor: { type: Object, required: true },
  // True when this sensor is the one shown in the detail panel
  selected: { type: Boolean, default: false },
});

defineEmits(["select"]);

const { label, tone, toneClasses } = useLabels();

const health = computed(() => props.sensor.health || "OFFLINE");
const dotClass = computed(
  () => toneClasses(tone("SensorHealth", health.value)).dot,
);

// The colour is not enough: screen readers get the state and the value in words
const ariaLabel = computed(() => {
  const value =
    props.sensor.last_value === null || props.sensor.last_value === undefined
      ? "sin lectura"
      : `${props.sensor.last_value} ${props.sensor.unit || "bar"}`;
  return `${props.sensor.name}: ${label("SensorHealth", health.value)}, ${value}`;
});
</script>
