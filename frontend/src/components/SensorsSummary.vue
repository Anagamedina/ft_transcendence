<!--
  SENSORS SUMMARY
  Presentational list of sensors for the admin dashboard. Receives data via props only.
  Status values follow the backend contract: ONLINE | OFFLINE.
  Async states (loading / error / empty) come from the parent via `status` and `error`;
  the retry is emitted so the parent re-runs the store action.
-->

<template>
  <section class="bg-white border border-gray-200 rounded-xl shadow-md p-5">
    <div class="flex items-center gap-2 mb-4">
      <span class="w-5 h-5 text-aqua-600"><AppIcon name="droplet" /></span>
      <h2 class="text-lg font-bold text-gray-800">Sensores</h2>
    </div>

    <LoadingState v-if="status === 'loading' || status === 'idle'" message="Cargando sensores…" compact />

    <ErrorState
      v-else-if="status === 'error'"
      title="No se han podido cargar los sensores"
      :message="error?.message"
      compact
      :autofocus="retried"
      @retry="onRetry"
    />

    <EmptyState
      v-else-if="sensors.length === 0"
      title="No hay sensores disponibles todavía"
      icon="droplet"
      compact
    />

    <ul v-else class="divide-y divide-gray-100">
      <li
        v-for="sensor in sensors"
        :key="sensor.id"
        class="py-3 flex items-center justify-between gap-3"
      >
        <div class="min-w-0">
          <p class="font-semibold text-gray-800 truncate">{{ sensor.name }}</p>
          <p class="text-sm text-gray-500 truncate">{{ sensor.location }}</p>
        </div>
        <span
          class="shrink-0 px-2 py-1 rounded-full text-xs font-semibold"
          :class="sensor.status === 'ONLINE'
            ? 'bg-success/10 text-success'
            : 'bg-gray-100 text-gray-500'"
        >
          {{ sensor.status === 'ONLINE' ? 'Online' : 'Offline' }}
        </span>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import AppIcon from './AppIcon.vue'
import LoadingState from './LoadingState.vue'
import ErrorState from './ErrorState.vue'
import EmptyState from './EmptyState.vue'

defineProps({
  sensors: { type: Array, default: () => [] },
  // Store status: idle | loading | success | error
  status: { type: String, default: 'success' },
  // Store error object ({ code, message, details }) or null
  error: { type: Object, default: null },
})

const emit = defineEmits(['retry'])

// After a user-triggered retry, a new error moves focus back to the retry button
const retried = ref(false)
function onRetry() {
  retried.value = true
  emit('retry')
}
</script>
