<template>
  <header
    :class="
      light
        ? 'sticky top-0 z-50 bg-white text-aqua-900 border-b border-aqua-100 shadow-sm'
        : 'relative bg-gradient-to-r from-aqua-600 to-aqua-400 text-white shadow-lg'
    "
  >
    <div
      class="relative z-10 flex flex-col sm:flex-row sm:justify-between sm:items-center px-4 py-3 sm:px-6 gap-3"
    >
      <!-- F29: same logo as the admin and client Sidebars -->
      <router-link
        to="/"
        class="hover:opacity-90 transition"
        aria-label="AquaGuard, ir a la portada"
      >
        <AppLogo :text="title" size="lg" />
      </router-link>
      <slot name="actions">
        <button
          class="bg-white text-aqua-600 px-4 py-2 md:px-6 rounded-lg font-semibold hover:bg-aqua-50 transition shrink-0"
        >
          Menu
        </button>
      </slot>
    </div>
  </header>
</template>

<script setup>
import AppLogo from "./AppLogo.vue";

defineProps({
  title: { type: String, default: "AquaGuard" },
  // Light variant (white background) used by the public area
  light: { type: Boolean, default: false },
});
</script>
