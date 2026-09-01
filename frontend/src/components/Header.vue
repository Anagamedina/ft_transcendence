<template>
  <header class="relative bg-aqua-900 text-white shadow-lg">
    <div class="relative z-10 flex justify-between items-center p-4 pl-16 md:pl-4 gap-2">
      <div class="flex items-center gap-3 flex-1 min-w-0">
        <div class="w-10 h-10 shrink-0 bg-white bg-opacity-20 rounded-full flex items-center justify-center text-xl">💧</div>
        <h1 class="title-clamp text-base sm:text-xl md:text-2xl font-bold flex-1 min-w-0">{{ title }}</h1>
      </div>
      <button class="bg-white text-aqua-600 px-4 py-2 md:px-6 rounded-lg font-semibold hover:bg-gray-100 transition shrink-0">
        Menu
      </button>
    </div>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, default: 'AquaGuard' }
})
</script>

<style scoped>
.title-clamp {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>