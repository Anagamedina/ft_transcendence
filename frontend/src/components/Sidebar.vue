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
    <nav class="space-y-1 flex-1" aria-label="Navegación principal">
      <template v-for="item in items" :key="item.label">
        <!-- Real link: highlighted when its route (or a child route) is open -->
        <router-link
          v-if="item.to"
          :to="item.to"
          class="flex items-center gap-3 px-4 py-3 rounded-lg transition"
          :class="isActive(item) ? 'bg-aqua-800 font-semibold' : 'hover:bg-aqua-800'"
          :aria-current="isActive(item) ? 'page' : undefined"
          @click="isOpen = false"
        >
          <span class="w-5 h-5 shrink-0"><AppIcon :name="item.icon" /></span>
          {{ item.label }}
        </router-link>

        <!-- No route yet: shown but not clickable -->
        <span
          v-else
          class="flex items-center gap-3 px-4 py-3 rounded-lg"
          :class="item.disabled ? 'opacity-50 cursor-not-allowed' : ''"
          :aria-disabled="item.disabled ? 'true' : undefined"
          :title="item.disabled ? 'Próximamente' : undefined"
        >
          <span class="w-5 h-5 shrink-0"><AppIcon :name="item.icon" /></span>
          {{ item.label }}
        </span>
      </template>
    </nav>
  </aside>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import AppIcon from './AppIcon.vue'

defineProps({
  appName: { type: String, default: 'AquaGuard' },
  // Each item: { label, icon, to?, exact?, disabled? }
  // Without items, the original three entries are shown (no links yet)
  items: {
    type: Array,
    default: () => [
      { label: 'Dashboard', icon: 'bar-chart' },
      { label: 'Sensores', icon: 'droplet' },
      { label: 'Alertas', icon: 'alert' },
    ],
  },
})

const isOpen = ref(false)
const route = useRoute()

// exact: only that path. Otherwise also its children (e.g. /admin/clients/:id)
function isActive(item) {
  if (item.exact) return route.path === item.to
  return route.path === item.to || route.path.startsWith(`${item.to}/`)
}
</script>