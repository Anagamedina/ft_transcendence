<!--
  SENSORS SUMMARY
  Presentational list of sensors for the admin dashboard. Receives sensors via props only.
  Status values follow the backend contract: ONLINE | OFFLINE.
-->

<template>
  <section class="bg-white border border-gray-200 rounded-xl shadow-md p-5">
    <div class="flex items-center gap-2 mb-4">
      <span class="w-5 h-5 text-aqua-600"><AppIcon name="droplet" /></span>
      <h2 class="text-lg font-bold text-gray-800">Sensores</h2>
    </div>

    <p v-if="sensors.length === 0" class="text-sm text-gray-500">
      No hay sensores disponibles todavía.
    </p>

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
import AppIcon from './AppIcon.vue'

defineProps({
  sensors: { type: Array, default: () => [] },
})
</script>