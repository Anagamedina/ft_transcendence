<!--
  ERROR STATE
  Shared feedback when an async request fails (store status === 'error').
  Shows a clear message and, optionally, a retry button that emits "retry".
  With `autofocus`, the retry button receives focus when the component appears,
  so keyboard users don't lose their place after a failed retry.
  Usage: <ErrorState :message="store.error?.message" @retry="store.fetchSensors()" />
-->

<template>
  <div
    role="alert"
    class="flex flex-col items-center justify-center gap-3 text-center rounded-xl border border-danger/40 bg-danger-light px-6"
    :class="compact ? 'py-6' : 'py-12'"
  >
    <div class="w-10 h-10 text-danger-dark">
      <AppIcon name="alert" />
    </div>
    <div class="flex flex-col gap-1">
      <p class="font-semibold text-danger-dark">{{ title }}</p>
      <p class="text-sm text-danger-dark">{{ message || defaultMessage }}</p>
    </div>
    <button
      v-if="retryable"
      ref="retryButton"
      type="button"
      class="min-h-[44px] px-5 rounded-lg border border-danger bg-white text-danger-dark font-semibold hover:bg-danger-light transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-danger"
      @click="$emit('retry')"
    >
      {{ retryText }}
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import AppIcon from "./AppIcon.vue";

const props = defineProps({
  title: { type: String, default: "No se han podido cargar los datos" },
  // Usually the store error message; falls back to a generic text
  message: { type: String, default: "" },
  // Show the retry button (the parent decides what to retry)
  retryable: { type: Boolean, default: true },
  retryText: { type: String, default: "Reintentar" },
  compact: { type: Boolean, default: false },
  // Move focus to the retry button on mount (use it after a user-triggered retry,
  // not on first page load, to avoid stealing focus)
  autofocus: { type: Boolean, default: false },
});

defineEmits(["retry"]);

const defaultMessage = "Comprueba la conexión e inténtalo de nuevo.";

const retryButton = ref(null);

onMounted(() => {
  if (props.autofocus) retryButton.value?.focus();
});
</script>
