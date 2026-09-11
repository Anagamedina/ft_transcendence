<template>
  <header
    class="relative bg-gradient-to-r from-[#0369A1] to-[#06B6D4] text-white shadow-lg"
  >
    <div
      class="relative z-10 flex flex-col sm:flex-row sm:justify-between sm:items-center p-4 gap-3"
    >
      <div class="flex items-center gap-3">
        <div
          class="w-10 h-10 shrink-0 bg-white bg-opacity-20 rounded-full flex items-center justify-center text-xl"
        >
          💧
        </div>
        <h1
          class="title-clamp text-base sm:text-xl md:text-2xl font-bold drop-shadow"
        >
          {{ title }}
        </h1>
      </div>
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
</style>
