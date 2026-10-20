<template>
  <!-- Menu button: only visible on mobile -->
  <button
    class="md:hidden fixed top-4 left-4 z-[60] bg-white text-aqua-900 border border-aqua-100 p-2 rounded-lg shadow-md"
    :aria-expanded="isOpen"
    aria-label="Abrir o cerrar el menú"
    @click="isOpen = !isOpen"
  >
    <span v-if="!isOpen">☰</span>
    <span v-else>✕</span>
  </button>

  <!-- Dark overlay behind the open menu on mobile.
       Layers: overlay (40) < sticky header and menu (50) < menu button (60).
       On desktop the menu has no z-index, so the sticky header stays on top. -->
  <div
    v-if="isOpen"
    class="md:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
    @click="isOpen = false"
  ></div>

  <aside
    class="w-64 bg-white text-slate-700 border-r border-aqua-100 px-4 pb-4 pt-20 md:pt-4 h-screen md:h-auto flex flex-col fixed md:static top-0 left-0 z-50 md:z-auto transition-transform duration-300"
    :class="isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'"
  >
    <h2 class="text-xl font-bold mb-6 text-aqua-900">{{ appName }}</h2>
    <nav class="space-y-1 flex-1" aria-label="Navegación principal">
      <div v-for="item in items" :key="item.label">
        <!-- Real link: highlighted when its route (or a child route) is open -->
        <router-link
          v-if="item.to"
          :to="item.to"
          class="flex items-center gap-3 px-4 py-3 rounded-lg transition"
          :class="
            isActive(item)
              ? 'bg-aqua-100 text-aqua-900 font-semibold'
              : 'hover:bg-aqua-50 hover:text-aqua-900'
          "
          :aria-current="isActive(item) ? 'page' : undefined"
          @click="isOpen = false"
        >
          <span class="w-5 h-5 shrink-0"><AppIcon :name="item.icon" /></span>
          {{ item.label }}
          <span
            v-if="item.badge"
            class="ml-auto rounded-full bg-danger-dark text-white px-2 py-0.5 text-xs font-semibold"
            :aria-label="`${item.badge} abiertas`"
          >
            {{ item.badge }}
          </span>
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
      </div>
    </nav>
  </aside>
</template>

<script setup>
import { ref } from "vue";
import { useRoute } from "vue-router";
import AppIcon from "./AppIcon.vue";

defineProps({
  appName: { type: String, default: "AquaGuard" },
  // Each item: { label, icon, to?, exact?, disabled?, badge? }
  // Without items, the original three entries are shown (no links yet)
  items: {
    type: Array,
    default: () => [
      { label: "Panel", icon: "bar-chart" },
      { label: "Sensores", icon: "droplet" },
      { label: "Alertas", icon: "alert" },
    ],
  },
});

const isOpen = ref(false);
const route = useRoute();

// exact: only that path. Otherwise also its children (e.g. /admin/clients/:id)
function isActive(item) {
  if (item.exact) return route.path === item.to;
  return route.path === item.to || route.path.startsWith(`${item.to}/`);
}
</script>
