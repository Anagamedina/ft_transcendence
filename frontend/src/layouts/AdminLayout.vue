<!--
  ADMIN LAYOUT
  Shared structure for admin pages (#252 design): soft turquoise Sidebar with
  the logo, the menu and who is logged in; the page content on the right.
  No top header: the logo and "Cerrar sesión" live in the Sidebar.
-->

<template>
  <div class="min-h-screen min-w-[320px] flex flex-col">
    <div class="flex flex-1">
      <Sidebar appName="Admin" :items="adminNav" tint>
        <template #brand>
          <router-link
            to="/admin"
            class="flex items-center gap-2 px-2"
            aria-label="AquaGuard, ir al panel"
          >
            <span class="water-drop" aria-hidden="true"></span>
            <span class="text-lg font-bold text-aqua-900">AquaGuard</span>
            <span
              class="rounded-full bg-white px-2 py-0.5 text-[11px] font-bold tracking-wider text-aqua-700"
              >ADMIN</span
            >
          </router-link>
        </template>
        <template #footer>
          <!-- Name and button on their own lines: the menu is too narrow for both -->
          <p class="flex flex-col items-start gap-0.5 px-2 text-sm text-slate-600">
            <span class="max-w-full truncate">{{ authStore.user?.name }}</span>
            <button
              type="button"
              class="font-semibold text-aqua-600 underline-offset-2 hover:underline disabled:opacity-50"
              :disabled="authStore.status === 'loading'"
              @click="handleLogout"
            >
              {{
                authStore.status === "loading"
                  ? "Cerrando sesión..."
                  : "Cerrar sesión"
              }}
            </button>
          </p>
        </template>
      </Sidebar>

      <!-- pt-16 on mobile: room for the Sidebar menu button (fixed top left) -->
      <main class="flex-1 min-w-0 bg-slate-50 p-6 pt-16 md:pt-6">
        <slot />
      </main>
    </div>

    <Footer />
  </div>
</template>

<script setup>
import Sidebar from "../components/Sidebar.vue";
import Footer from "../components/Footer.vue";

import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useOverviewStore } from "../stores/overview";

const router = useRouter();
const authStore = useAuthStore();
const overviewStore = useOverviewStore();

// Open alerts come from the server (/api/analytics/overview), the same number as
// the Panel KPI. Before it counted the first 100 alerts loaded in the browser.
const openAlerts = computed(() => overviewStore.overview?.open_alerts ?? 0);
const criticalOpen = computed(
  () => overviewStore.overview?.critical_open_alerts ?? 0,
);

const adminNav = computed(() => [
  { label: "Panel", to: "/admin", icon: "bar-chart", exact: true },
  { label: "Clientes", to: "/admin/clients", icon: "users" },
  { label: "Edificios", to: "/admin/sites", icon: "building" },
  { label: "Sensores", to: "/admin/sensors", icon: "droplet" },
  {
    label: "Alertas",
    to: "/admin/alerts",
    icon: "alert",
    badge: openAlerts.value,
    badgeAlert: criticalOpen.value > 0,
    badgeTitle:
      `${openAlerts.value} abiertas` +
      (criticalOpen.value > 0 ? `, ${criticalOpen.value} críticas` : ""),
  },
  { label: "Mi cuenta", to: "/admin/account", icon: "user" },
]);

// Pages that do not load the overview themselves still need the counter.
onMounted(async () => {
  if (overviewStore.status !== "idle") return;
  try {
    await overviewStore.fetchOverview();
  } catch {
    /* handled via overviewStore.error */
  }
});

async function handleLogout() {
  await authStore.logout();
  await router.replace("/login");
}
</script>

<style scoped>
/* Same drop as the public header logo, smaller */
.water-drop {
  width: 18px;
  height: 22px;
  background: #06b6d4;
  border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
  transform: rotate(0deg);
  clip-path: polygon(50% 0, 100% 62%, 92% 85%, 72% 98%, 28% 98%, 8% 85%, 0 62%);
}
</style>
