<!--
  ERROR STATE
  Shared feedback when an async request fails (store status === 'error').
  Shows a clear message and, optionally, a retry button that emits "retry".
  Usage: <ErrorState :message="store.error?.message" @retry="store.fetchSensors()" />
-->

<template>
  <div
    role="alert"
    class="flex flex-col items-center justify-center gap-3 text-center rounded-xl border border-red-200 bg-red-50 px-6"
    :class="compact ? 'py-6' : 'py-12'"
  >
    <div class="w-10 h-10 text-red-700">
      <AppIcon name="alert" />
    </div>
    <div class="flex flex-col gap-1">
      <p class="font-semibold text-red-800">{{ title }}</p>
      <p class="text-sm text-red-700">{{ message || defaultMessage }}</p>
    </div>
    <button
      v-if="retryable"
      type="button"
      class="min-h-[44px] px-5 rounded-lg border border-red-700 bg-white text-red-700 font-semibold hover:bg-red-100 transition"
      @click="$emit('retry')"
    >
      {{ retryText }}
    </button>
  </div>
</template>

<script setup>
import AppIcon from "./AppIcon.vue";

defineProps({
  title: { type: String, default: "No se han podido cargar los datos" },
  // Usually the store error message; falls back to a generic text
  message: { type: String, default: "" },
  // Show the retry button (the parent decides what to retry)
  retryable: { type: Boolean, default: true },
  retryText: { type: String, default: "Reintentar" },
  compact: { type: Boolean, default: false },
});

defineEmits(["retry"]);

const defaultMessage = "Comprueba la conexión e inténtalo de nuevo.";
</script>
