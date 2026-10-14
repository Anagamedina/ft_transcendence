<!-- CLIENT LAYOUT — sidebar cliente; sensores, histórico, alertas, perfil. -->

<template>
  <div class="min-h-screen min-w-[320px] flex flex-col">
    <Header title="AquaGuard">
      <template #actions>
        <button
          type="button"
          class="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50"
          :disabled="authStore.status === 'loading'"
          @click="handleLogout"
        >
          {{
            authStore.status === 'loading'
              ? 'Cerrando sesión...'
              : 'Cerrar sesión'
          }}
        </button>
      </template>
    </Header>

    <div class="flex flex-1 overflow-hidden">
      <Sidebar
        appName="AquaGuard"
        :items="sidebarItems"
      />

      <main class="min-w-0 flex-1 overflow-y-auto bg-slate-50 p-6">
        <RouterView />
      </main>
    </div>

    <Footer />
  </div>
</template>

<script setup>
import { useRouter, RouterView } from 'vue-router'
import { useAuthStore } from '../stores/auth'

import Header from '../components/Header.vue'
import Sidebar from '../components/Sidebar.vue'
import Footer from '../components/Footer.vue'

const router = useRouter()
const authStore = useAuthStore()

const sidebarItems = [
  { label: 'Dashboard', to: '/app', icon: 'building'},
  { label: 'Sensores', to: '/app#sensors', icon: 'droplet'},
  { label: 'Histórico', to: '/app#history', icon: 'bar-chart' },
  { label: 'Alertas', to: '/app#alerts', icon: 'alert'},
  { label: 'Perfil', to: '/app#profile', icon: 'users' },
]

async function handleLogout() {
  await authStore.logout()
  await router.replace('/login')
}
</script>
