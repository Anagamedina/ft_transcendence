<!--
  ADMIN LAYOUT
  Shared structure for admin pages: Header, Sidebar, Footer and a slot for page content.
-->

<template>
  <div class="min-h-screen min-w-[320px] flex flex-col">
    <!-- pl-12 on mobile: room for the Sidebar menu button, which is fixed at the top left -->
    <Header title="AquaGuard · Admin" class="pl-12 md:pl-0">
      <template #actions>
        <button
          @click="handleLogout"
          :disabled="authStore.status === 'loading'"
          class="bg-white text-aqua-600 px-4 py-2 rounded-lg font-semibold hover:bg-gray-100 transition shrink-0 disabled:opacity-50"
        >
          {{ authStore.status === 'loading' ? 'Cerrando sesión...' : 'Cerrar sesión' }}
        </button>
      </template>
    </Header>

    <div class="flex flex-1">
      <Sidebar appName="Admin" :items="adminNav" />

      <main class="flex-1 min-w-0 bg-slate-100 p-6">
        <slot />
      </main>
    </div>

    <Footer />
  </div>
</template>

<script setup>
import Header from "../components/Header.vue";
import Sidebar from "../components/Sidebar.vue";
import Footer from "../components/Footer.vue";

import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useAlertsStore } from "../stores/alerts";

const router = useRouter();
const authStore = useAuthStore();
const alertsStore = useAlertsStore();

// Admin menu. The alerts entry shows how many alerts are still open.
const adminNav = computed(() => [
  { label: "Panel", to: "/admin", icon: "bar-chart", exact: true },
  { label: "Clientes", to: "/admin/clients", icon: "users" },
  { label: "Edificios", to: "/admin/sites", icon: "building" },
  { label: "Sensores", to: "/admin/sensors", icon: "droplet" },
  { label: "Alertas", to: "/admin/alerts", icon: "alert", badge: alertsStore.openCount },
]);

// Pages that do not load the alerts themselves still need the counter.
onMounted(async () => {
  if (alertsStore.status !== "idle") return;
  try { await alertsStore.fetchAlerts() } catch { /* handled via alertsStore.error */ }
});

async function handleLogout() {
  await authStore.logout();
  await router.replace("/login");
}

</script>