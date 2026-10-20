<!-- CLIENT LAYOUT: header, trial banner, client sidebar and page content. -->

<template>
  <div class="min-h-screen min-w-[320px] flex flex-col">
    <Header title="AquaGuard" light class="pl-12 md:pl-0">
      <template #actions>
        <div class="flex items-center gap-3">
          <span class="hidden text-sm font-medium sm:inline">
            {{ organizationName }}
          </span>
          <button
            type="button"
            class="border border-aqua-600 text-aqua-600 px-4 py-2 rounded-lg font-semibold text-sm hover:bg-aqua-50 transition disabled:opacity-50"
            :disabled="authStore.status === 'loading'"
            @click="handleLogout"
          >
            {{
              authStore.status === "loading"
                ? "Cerrando sesión..."
                : "Cerrar sesión"
            }}
          </button>
        </div>
      </template>
    </Header>

    <TrialBanner :organization="authStore.organization" />

    <div class="flex flex-1 overflow-hidden">
      <Sidebar appName="AquaGuard" :items="sidebarItems" />

      <main class="min-w-0 flex-1 overflow-y-auto bg-aqua-50 p-6">
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

import Header from "../components/Header.vue";
import Sidebar from "../components/Sidebar.vue";
import Footer from "../components/Footer.vue";
import TrialBanner from "../components/TrialBanner.vue";

const router = useRouter();
const authStore = useAuthStore();
const overviewStore = useOverviewStore();

const organizationName = computed(
  () => authStore.organization?.name || "Mi organización",
);

// TODO: connect the badge to the exact active-alert field
// defined by GET /api/analytics/overview.
const activeAlertCount = computed(() => {
  return overviewStore.overview?.open_alerts ?? 0;
});

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
    badge: activeAlertCount.value,
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
