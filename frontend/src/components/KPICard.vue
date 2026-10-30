<!--
  KPI CARD
  Presentational card for a single dashboard metric. Receives data via props only.
-->

<template>
  <div
    class="bg-white border border-slate-200 rounded-xl p-5 shadow-md flex items-center gap-4"
  >
    <div
      class="w-12 h-12 shrink-0 rounded-full bg-aqua-50 text-aqua-600 flex items-center justify-center p-3"
    >
      <slot name="icon" />
    </div>
    <div>
      <p class="text-sm text-slate-500">{{ label }}</p>
      <p class="text-2xl font-bold text-slate-800">{{ value }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [Number, String], default: "—" },
});
</script>
