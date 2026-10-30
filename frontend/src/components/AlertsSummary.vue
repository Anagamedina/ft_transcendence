<!--
  ALERTS SUMMARY
  Presentational list of alerts for the admin dashboard. Receives data via props only.
  Values follow the backend contract: severity WARNING | CRITICAL.
  Async states (loading / error / empty) come from the parent via `status` and `error`;
  the retry is emitted so the parent re-runs the store action.
  No actions here: acknowledging/resolving alerts belongs to another issue.
-->

<template>
  <section class="bg-white border border-slate-200 rounded-xl shadow-md p-5">
    <div class="flex items-center gap-2 mb-4">
      <span class="w-5 h-5 text-aqua-600"><AppIcon name="alert" /></span>
      <h2 class="text-lg font-bold text-slate-800">Alertas activas</h2>
    </div>

    <LoadingState
      v-if="status === 'loading' || status === 'idle'"
      message="Cargando alertas…"
      compact
    />

    <ErrorState
      v-else-if="status === 'error'"
      title="No se han podido cargar las alertas"
      :message="error?.message"
      compact
      :autofocus="retried"
      @retry="onRetry"
    />

    <EmptyState
      v-else-if="alerts.length === 0"
      title="No hay alertas activas"
      icon="alert"
      compact
    />

    <ul v-else class="divide-y divide-slate-100">
      <li
        v-for="alert in alerts"
        :key="alert.id"
        class="py-3 flex items-start justify-between gap-3"
      >
        <div class="min-w-0">
          <p class="font-semibold text-slate-800">
            {{ label("AlertType", alert.type) }}
          </p>
          <p class="text-sm text-slate-500">{{ alert.message }}</p>
          <p class="text-xs text-slate-500 mt-1">
            {{ formatDateTime(alert.created_at) }}
          </p>
        </div>
        <StatusPill
          type="AlertSeverity"
          :value="alert.severity"
          class="shrink-0"
        />
      </li>
    </ul>
  </section>
</template>

<script setup>
import { ref } from "vue";
import AppIcon from "./AppIcon.vue";
import StatusPill from "./StatusPill.vue";
import LoadingState from "./LoadingState.vue";
import ErrorState from "./ErrorState.vue";
import EmptyState from "./EmptyState.vue";
import { useLabels } from "../composables/useLabels";
import { useFormat } from "../composables/useFormat";

defineProps({
  alerts: { type: Array, default: () => [] },
  // Store status: idle | loading | success | error
  status: { type: String, default: "success" },
  // Store error object ({ code, message, details }) or null
  error: { type: Object, default: null },
});

const emit = defineEmits(["retry"]);

// After a user-triggered retry, a new error moves focus back to the retry button
const retried = ref(false);
function onRetry() {
  retried.value = true;
  emit("retry");
}

// Same texts and colours as the alerts table; dates in local time ('hoy 08:20')
const { label } = useLabels();
const { formatDateTime } = useFormat();
</script>
