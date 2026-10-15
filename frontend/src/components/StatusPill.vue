<!--
  STATUS PILL
  Coloured pill for any backend status enum. Text and colour come from
  useLabels, so every screen shows the same state the same way.
  Replaces the empty StatusBadge.vue.
  Usage:
    <StatusPill type="AlertSeverity" :value="alert.severity" />
    <StatusPill type="SensorHealth" value="OFFLINE" size="md" />
-->

<template>
  <span
    class="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full font-medium"
    :class="[
      classes.pill,
      size === 'md' ? 'px-3 py-1 text-sm' : 'px-2.5 py-1 text-xs',
    ]"
  >
    <span
      class="h-1.5 w-1.5 rounded-full"
      :class="classes.dot"
      aria-hidden="true"
    ></span>
    {{ text }}
  </span>
</template>

<script setup>
import { computed } from "vue";
import { useLabels } from "../composables/useLabels";

const props = defineProps({
  // Enum name as in enums.py: 'AlertSeverity', 'AlertState', 'SensorHealth'...
  type: { type: String, required: true },
  // Enum value, e.g. 'CRITICAL'
  value: { type: String, default: null },
  // 'sm' for tables and cards, 'md' for detail headers
  size: {
    type: String,
    default: "sm",
    validator: (v) => ["sm", "md"].includes(v),
  },
});

const { label, tone, toneClasses } = useLabels();

const text = computed(() => label(props.type, props.value));
const classes = computed(() => toneClasses(tone(props.type, props.value)));
</script>
