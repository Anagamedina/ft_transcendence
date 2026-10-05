<!--
  EMPTY STATE
  Shared feedback when a request succeeds but returns no items.
  The optional "action" slot holds a call to action (e.g. "Nuevo cliente").
  Usage:
    <EmptyState title="Todavía no hay clientes" message="Crea el primero para empezar.">
      <template #action><button …>Nuevo cliente</button></template>
    </EmptyState>
-->

<template>
  <div
    class="flex flex-col items-center justify-center gap-3 text-center rounded-xl border border-dashed border-gray-300 bg-white px-6"
    :class="compact ? 'py-6' : 'py-12'"
  >
    <div class="w-10 h-10 text-aqua-600">
      <AppIcon :name="icon" />
    </div>
    <div class="flex flex-col gap-1">
      <p class="font-semibold text-gray-800">{{ title }}</p>
      <p v-if="message" class="text-sm text-gray-600">{{ message }}</p>
    </div>
    <div v-if="$slots.action">
      <slot name="action" />
    </div>
  </div>
</template>

<script setup>
import AppIcon from "./AppIcon.vue";

defineProps({
  title: { type: String, default: "No hay datos todavía" },
  message: { type: String, default: "" },
  // Any icon name supported by AppIcon (building, droplet, wifi, alert, bar-chart)
  icon: { type: String, default: "droplet" },
  compact: { type: Boolean, default: false },
});
</script>
