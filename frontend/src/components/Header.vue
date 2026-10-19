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
      <router-link
        to="/"
        class="flex items-center gap-2 hover:opacity-90 transition"
        aria-label="AquaGuard, ir a la portada"
      >
        <div class="water-drop-header"></div>
        <h1
          :class="[
            'title-clamp text-xl sm:text-2xl font-bold',
            light ? '' : 'drop-shadow',
          ]"
        >
          {{ title }}
        </h1>
      </router-link>
      <slot name="actions">
        <button
          class="bg-white text-aqua-600 px-4 py-2 md:px-6 rounded-lg font-semibold hover:bg-gray-100 transition shrink-0"
        >
          Menu
        </button>
      </slot>
    </div>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, default: "AquaGuard" },
  // Light variant (white background) used by the public area
  light: { type: Boolean, default: false },
});
</script>

<style scoped>
.title-clamp {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.water-drop-header {
  width: 26px;
  height: 26px;
  background: linear-gradient(
    135deg,
    white 0%,
    theme('colors.aqua.300') 45%,
    theme('colors.aqua.600') 100%
  );
  border-radius: 50% 50% 50% 0;
  transform: rotate(135deg);
  box-shadow:
    inset -3px -3px 8px rgb(255 255 255 / 0.4),
    3px 3px 10px theme('colors.aqua.600 / 30%');
}
</style>
