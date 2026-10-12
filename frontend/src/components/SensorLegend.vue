<!--
  SENSOR LEGEND
  Explains the sensor health states used in the building view (F4), with the
  same coloured dot as SensorPin. Four states (team decision): Normal, Aviso,
  Crítico and Sin conexión. Optional counts show how many sensors are in each.
  Usage:
    <SensorLegend />
    <SensorLegend :counts="{ OK: 3, WARNING: 1, CRITICAL: 0, OFFLINE: 2 }" />
-->

<template>
  <ul class="flex flex-wrap gap-x-3.5 gap-y-1 text-xs text-slate-600" aria-label="Leyenda de estados de los sensores">
    <li v-for="item in items" :key="item.key" class="flex items-center gap-1.5">
      <span class="h-[9px] w-[9px] rounded-full" :class="item.dot" aria-hidden="true"></span>
      {{ item.text }}
      <span v-if="counts" class="font-semibold tabular-nums text-slate-800">{{ item.count }}</span>
    </li>
  </ul>
</template>

<script setup>
import { computed } from 'vue'
import { useLabels } from '../composables/useLabels'
import { HEALTH_ORDER } from '../utils/sensorHealth'

const props = defineProps({
  // Optional { OK, WARNING, CRITICAL, OFFLINE } counters (see countByHealth)
  counts: { type: Object, default: null },
})

const { label, tone, toneClasses } = useLabels()

const items = computed(() =>
  HEALTH_ORDER.map((key) => ({
    key,
    text: label('SensorHealth', key),
    dot: toneClasses(tone('SensorHealth', key)).dot,
    count: props.counts?.[key] ?? 0,
  })),
)
</script>
