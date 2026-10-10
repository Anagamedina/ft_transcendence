<!--
  LOADING STATE
  Shared feedback while async data is loading (store status === 'loading').
  Announced politely to screen readers; the spinner respects reduced motion.
  Usage: <LoadingState message="Cargando clientes…" />
-->

<template>
  <div
    role="status"
    aria-live="polite"
    class="flex flex-col items-center justify-center gap-3 text-center"
    :class="compact ? 'py-6' : 'py-16'"
  >
    <span
      aria-hidden="true"
      class="inline-block rounded-full border-4 border-aqua-100 border-t-aqua-600 motion-safe:animate-spin"
      :class="compact ? 'w-6 h-6' : 'w-10 h-10'"
    ></span>
    <p class="text-sm text-gray-600">{{ message }}</p>
  </div>
</template>

<script setup>
defineProps({
  // Text shown under the spinner and read by screen readers
  message: { type: String, default: "Cargando…" },
  // Smaller version for use inside cards or table bodies
  compact: { type: Boolean, default: false },
});
</script>
