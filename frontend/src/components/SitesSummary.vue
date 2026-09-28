<!--
  SITES SUMMARY
  Presentational list of sites for the admin dashboard. Receives sites via props only.
-->

<template>
  <section class="bg-white border border-gray-200 rounded-xl shadow-md p-5">
    <div class="flex items-center gap-2 mb-4">
      <span class="w-5 h-5 text-aqua-600"><AppIcon name="building" /></span>
      <h2 class="text-lg font-bold text-gray-800">Sites</h2>
    </div>

    <p v-if="sites.length === 0" class="text-sm text-gray-500">
      No hay sites disponibles todavía.
    </p>

    <ul v-else class="divide-y divide-gray-100">
      <li v-for="site in sites" :key="site.id" class="py-3">
        <p class="font-semibold text-gray-800">{{ site.name }}</p>
        <p class="text-sm text-gray-500">{{ site.address }}</p>
      </li>
    </ul>
  </section>
</template>

<script setup>
import AppIcon from './AppIcon.vue'

defineProps({
  sites: { type: Array, default: () => [] },
})
</script>