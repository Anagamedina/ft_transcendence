<!--
  ADMIN LAYOUT
  Shared structure for admin pages: Header, Sidebar, Footer and a slot for page content.
-->

<template>
  <div class="min-h-screen min-w-[320px] flex flex-col">
    <Header title="AquaGuard · Admin">
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

    <div class="flex flex-1 overflow-hidden">
      <Sidebar appName="Admin" :items="adminNav" />

      <main class="flex-1 overflow-y-auto bg-slate-100 p-6">
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

// Admin menu. Sensors and alerts have no admin route yet (data area, #38)
const adminNav = [
  { label: "Dashboard", to: "/admin", icon: "bar-chart", exact: true },
  { label: "Clientes", to: "/admin/clients", icon: "users" },
  { label: "Sites", to: "/admin/sites", icon: "building" },
  { label: "Sensores", icon: "droplet", disabled: true },
  { label: "Alertas", icon: "alert", disabled: true },
];

import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();

async function handleLogout() {
  await authStore.logout();
  await router.replace("/login");
}

</script>