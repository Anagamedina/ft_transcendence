<template>
  <header
    class="relative bg-gradient-to-r from-[#0369A1] to-[#06B6D4] text-white shadow-lg"
  >
    <div
      class="relative z-10 flex flex-col sm:flex-row sm:justify-between sm:items-center p-4 gap-3"
    >
    <router-link to="/" class="flex items-center gap-1.5 hover:opacity-90 transition">
      <div class="water-drop-header"></div>
      <h1
        class="title-clamp text-base sm:text-xl md:text-2xl font-bold drop-shadow"
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
  background: linear-gradient(135deg, #ffffff 0%, #a5f3fc 45%, #0369a1 100%);
  border-radius: 50% 50% 50% 0;
  transform: rotate(135deg);
  box-shadow:
    inset -3px -3px 8px rgba(255, 255, 255, 0.4),
    3px 3px 10px rgba(3, 105, 161, 0.3);
}
</style>
