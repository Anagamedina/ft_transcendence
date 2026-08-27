<template>
  <aside class="w-64 bg-gray-800 text-white p-4">
    <h2 class="text-lg font-bold mb-4">{{ appName }}</h2>
    <nav class="space-y-2">
      <a href="#" class="block p-2 hover:bg-gray-700 rounded">Inicio</a>
      <a href="#" class="block p-2 hover:bg-gray-700 rounded">Sensores</a>
      <a href="#" class="block p-2 hover:bg-gray-700 rounded">Alertas</a>
    </nav>
  </aside>
</template>

<script setup>
defineProps({
  appName: String
})
</script>