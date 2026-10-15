<template>
  <footer
    :class="
      light
        ? 'bg-[#e6f4f8] text-slate-700 border-t border-aqua-100'
        : 'bg-aqua-900 text-gray-300'
    "
    class="mt-auto"
  >
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
          :class="
            light ? 'text-aqua-600 hover:text-aqua-900' : 'hover:text-aqua-200'
          "
          class="transition"
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
  // Light variant for the public pages; the default dark one is used in the app
  light: { type: Boolean, default: false },
});

const year = new Date().getFullYear();

const links = [
  { to: "/legal#privacidad", label: "Política de privacidad" },
  { to: "/legal#terminos", label: "Términos de servicio" },
  { to: "/status", label: "Estado del servicio" },
];
</script>
