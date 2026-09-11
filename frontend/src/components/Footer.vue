<template>
  <footer
    :class="dark ? 'bg-[#0F172A]' : 'bg-aqua-900'"
    class="text-gray-300 mt-auto"
  >
    <div
      class="w-full px-4 py-6 flex flex-col sm:flex-row justify-between items-center gap-3 text-sm"
    >
      <p>© {{ year }} {{ appName }}. Todos los derechos reservados.</p>
      <nav class="flex gap-6">
        <router-link to="/privacy" class="hover:text-aqua-200 transition"
          >Política de Privacidad</router-link
        >
        <router-link to="/terms" class="hover:text-aqua-200 transition"
          >Términos de Servicio</router-link
        >
      </nav>
    </div>
  </footer>
</template>

<script setup>
defineProps({
  appName: { type: String, default: "AquaGuard" },
  dark: { type: Boolean, default: false },
});

const year = new Date().getFullYear();
</script>
