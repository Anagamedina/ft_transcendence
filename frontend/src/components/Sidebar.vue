<template>
  <!-- Botón hamburguesa: solo visible en móvil -->
  <button
    class="md:hidden fixed top-4 left-4 z-50 bg-aqua-900 text-white p-2 rounded-lg shadow-lg"
    @click="isOpen = !isOpen"
  >
    <span v-if="!isOpen">☰</span>
    <span v-else>✕</span>
  </button>

  <!-- Overlay oscuro al abrir en móvil -->
  <div
    v-if="isOpen"
    class="md:hidden fixed inset-0 bg-black bg-opacity-50 z-30"
    @click="isOpen = false"
  ></div>

  <aside
    class="w-64 bg-aqua-900 text-white p-4 h-screen md:h-auto flex flex-col fixed md:static top-0 left-0 z-40 transition-transform duration-300"
    :class="isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'"
  >
    <h2 class="text-xl font-bold mb-6 text-aqua-200">{{ appName }}</h2>
    <nav class="space-y-1 flex-1">
      <a href="#" class="block px-4 py-3 hover:bg-aqua-800 rounded-lg transition">📊 Dashboard</a>
      <a href="#" class="block px-4 py-3 hover:bg-aqua-800 rounded-lg transition">💧 Sensores</a>
      <a href="#" class="block px-4 py-3 hover:bg-aqua-800 rounded-lg transition">⚠️ Alertas</a>
    </nav>
  </aside>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  appName: { type: String, default: 'AquaGuard' }
})

const isOpen = ref(false)
</script>