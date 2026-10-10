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
        <!-- Renders a button when selectable (keyboard accessible), a plain div otherwise -->
                <!-- Renders a button when selectable (keyboard accessible), a plain div otherwise -->
        <component
          :is="selectable ? 'button' : 'div'"
          :type="selectable ? 'button' : undefined"
          class="group w-full text-left rounded-lg flex items-center justify-between gap-3"
          :class="selectable
            ? 'px-3 py-2 border-l-4 border-transparent hover:border-aqua-500 hover:bg-aqua-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-aqua-500 transition'
            : ''"
          @click="selectable && $emit('select', site)"
        >
          <div>
            <p
              class="font-semibold text-gray-800 transition"
              :class="selectable ? 'group-hover:text-aqua-700' : ''"
            >
              {{ site.name }}
            </p>
            <p class="text-sm text-gray-500">{{ site.address }}</p>
          </div>

          <!-- Arrow hint, only when the site is clickable -->
          <span
            v-if="selectable"
            aria-hidden="true"
            class="text-xl text-gray-400 group-hover:text-aqua-600 group-hover:translate-x-1 transition"
          >›</span>
        </component>
      </li>
    </ul>
  </section>
</template>
<script setup>
import AppIcon from './AppIcon.vue'

defineProps({
  sites: { type: Array, default: () => [] },
  // When true, each site is clickable and emits 'select'
  selectable: { type: Boolean, default: false },
})

defineEmits(['select'])
</script>