<template>
  <footer class="bg-aqua-900 text-gray-300 mt-auto">
    <div class="max-w-7xl mx-auto px-6 py-6 flex flex-col sm:flex-row justify-between items-center gap-3 text-sm">
      <p>© {{ year }} {{ appName }}. Todos los derechos reservados.</p>
      <nav class="flex gap-6">
        <router-link to="/privacy" class="hover:text-aqua-200 transition">Privacy Policy</router-link>
        <router-link to="/terms" class="hover:text-aqua-200 transition">Terms of Service</router-link>
      </nav>
    </div>
  </footer>
</template>

<script setup>
defineProps({
  appName: { type: String, default: 'AquaGuard' }
})

const year = new Date().getFullYear()
</script>