<template>
  <!-- Single light footer for every layout (public, admin and client), as in the mockup -->
  <footer class="mt-auto bg-aqua-75 text-slate-700 border-t border-aqua-100">
    <div
      class="w-full px-6 py-5 flex flex-col sm:flex-row justify-between items-center gap-3 text-sm"
    >
      <p>© {{ year }} {{ appName }} · Barcelona</p>
      <nav
        aria-label="Enlaces legales"
        class="flex flex-wrap justify-center gap-x-6 gap-y-2"
      >
        <router-link
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="text-aqua-600 hover:text-aqua-900 transition"
        >
          {{ link.label }}
        </router-link>
      </nav>
    </div>
  </footer>
</template>

<script setup>
defineProps({
  appName: { type: String, default: "AquaGuard" },
});

const year = new Date().getFullYear();

const links = [
  { to: "/legal#privacidad", label: "Política de privacidad" },
  { to: "/legal#terminos", label: "Términos de servicio" },
  { to: "/status", label: "Estado del servicio" },
];
</script>
