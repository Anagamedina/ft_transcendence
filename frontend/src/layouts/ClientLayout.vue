<!--
  CLIENT LAYOUT
  Same structure as AdminLayout (#252 design), so both panels look alike (F27):
  soft turquoise Sidebar with the logo, the menu and who is logged in; the page
  content on the right. No top header: the logo and "Cerrar sesión" live in
  the Sidebar. The trial notice (TrialBanner) opens the page content.
-->

<template>
  <div class="min-h-screen min-w-[320px] flex flex-col">
    <div class="flex flex-1">
      <Sidebar appName="AquaGuard" :items="sidebarItems" tint>
        <template #brand>
          <router-link
            to="/app"
            class="flex items-center gap-2 px-2"
            aria-label="AquaGuard, ir a Mis edificios"
          >
            <span class="water-drop" aria-hidden="true"></span>
            <span class="text-lg font-bold text-aqua-900">AquaGuard</span>
          </router-link>
        </template>
        <template #footer>
          <!-- Name, organization and button on their own lines: the menu is narrow -->
          <p class="flex flex-col items-start gap-0.5 px-2 text-sm text-slate-600">
            <span class="max-w-full truncate font-medium text-slate-800">{{
              authStore.user?.name
            }}</span>
            <span class="max-w-full truncate">{{ organizationName }}</span>
            <button
              type="button"
              class="mt-1 font-semibold text-aqua-600 underline-offset-2 hover:underline disabled:opacity-50"
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
        <TrialBanner
          :organization="authStore.organization"
          class="mb-6 rounded-lg border"
        />
        <RouterView />
      </main>
    </div>

    <Footer />
  </div>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { useRouter, RouterView } from "vue-router";

import { useAuthStore } from "../stores/auth";
import { useOverviewStore } from "../stores/overview";
import { useAutoRefresh } from "../composables/useAutoRefresh";

import Sidebar from "../components/Sidebar.vue";
import Footer from "../components/Footer.vue";
import TrialBanner from "../components/TrialBanner.vue";

const router = useRouter();
const authStore = useAuthStore();
const overviewStore = useOverviewStore();

const organizationName = computed(
  () => authStore.organization?.name || "Mi organización",
);

// Open alerts of this organization (GET /api/analytics/overview), the same
// counter and red dot as the admin menu
const openAlerts = computed(() => overviewStore.overview?.open_alerts ?? 0);
const criticalOpen = computed(
  () => overviewStore.overview?.critical_open_alerts ?? 0,
);

const sidebarItems = computed(() => [
  {
    label: "Mis edificios",
    to: "/app",
    icon: "building",
    exact: true,
  },
  {
    label: "Alertas",
    to: "/app/alerts",
    icon: "alert",
    badge: openAlerts.value,
    badgeAlert: criticalOpen.value > 0,
    badgeTitle:
      `${openAlerts.value} abiertas` +
      (criticalOpen.value > 0 ? `, ${criticalOpen.value} críticas` : ""),
  },
  {
    label: "Documentos",
    to: "/app/documents",
    icon: "file-text",
  },
  {
    label: "Mi cuenta",
    to: "/app/account",
    icon: "user",
  },
]);

async function refreshOverview() {
  try {
    await overviewStore.fetchOverview();
  } catch {
    // Keep the layout usable when analytics is unavailable.
  }
}

useAutoRefresh(refreshOverview, 30000);

onMounted(refreshOverview);

async function handleLogout() {
  await authStore.logout();
  await router.replace("/login");
}
</script>

<style scoped>
/* Same drop as AdminLayout and the public header logo */
.water-drop {
  width: 18px;
  height: 22px;
  background: #06b6d4;
  border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
  clip-path: polygon(50% 0, 100% 62%, 92% 85%, 72% 98%, 28% 98%, 8% 85%, 0 62%);
}
</style>
