<!-- CLIENT LAYOUT — sidebar cliente; sensores, histórico, alertas, perfil. -->

<template>
  <div class="min-h-screen min-w-[320px] flex flex-col">
    <Header title="AquaGuard">
      <template #actions>
        <div class="flex items-center gap-3">
          <span class="hidden text-sm font-medium sm:inline">
            {{ organizationName }}
          </span>
          <button
            type="button"
            class="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50"
            :disabled="authStore.status === 'loading'"
            @click="handleLogout"
          >
            {{ authStore.status === 'loading'
              ? 'Cerrando sesión...'
              : 'Cerrar sesión' }}
          </button>
        </div>
      </template>
    </Header>

    <div
      v-if="trialDays !== null"
      class="border-b border-amber-200 bg-amber-50 px-6 py-3 text-sm text-amber-900"
      role="status"
    >
      <strong>Periodo de prueba:</strong>
      <template v-if="trialDays > 1">
        quedan {{ trialDays }} días.
      </template>
      <template v-else-if="trialDays === 1">
        queda 1 día.
      </template>
      <template v-else>
        la prueba termina hoy.
      </template>
    </div>

    <div class="flex flex-1 overflow-hidden">
      <Sidebar appName="AquaGuard" :items="sidebarItems" />

      <main class="min-w-0 flex-1 overflow-y-auto bg-slate-50 p-6">
        <RouterView />
      </main>
    </div>

    <Footer />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter, RouterView } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import { useOverviewStore } from '../stores/overview'
import { useAutoRefresh } from '../composables/useAutoRefresh'

import Header from '../components/Header.vue'
import Sidebar from '../components/Sidebar.vue'
import Footer from '../components/Footer.vue'

const router = useRouter()
const authStore = useAuthStore()
const overviewStore = useOverviewStore()

const organizationName = computed(
  () => authStore.organization?.name || 'Mi organización'
)

const trialDays = computed(() => {
  const organization = authStore.organization

  if (
    organization?.status !== 'TRIAL' ||
    !organization.trial_ends_at
  ) {
    return null
  }

  const end = new Date(organization.trial_ends_at)
  if (Number.isNaN(end.getTime())) return null

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  end.setHours(0, 0, 0, 0)

  return Math.max(
    0,
    Math.round((end - today) / (24 * 60 * 60 * 1000))
  )
})

// TODO: connect the badge to the exact active-alert field
// defined by GET /api/analytics/overview.
const activeAlertCount = computed(() => {
  return overviewStore.overview?.open_alerts ?? 0
})

const sidebarItems = computed(() => [
  {
    label: 'Mis edificios',
    to: '/app',
    icon: 'building',
    exact: true,
  },
  {
    label: 'Alertas',
    to: null,
    icon: 'alert',
    badge: activeAlertCount.value,
    disabled: true,
  },
  {
    label: 'Documentos',
    to: null,
    icon: 'file-text',
    disabled: true,
  },
  {
    label: 'Mi cuenta',
    to: '/app/account',
    icon: 'users',
  },
])

async function refreshOverview() {
  try {
    await overviewStore.fetchOverview()
  } catch {
    // Keep the layout usable when analytics is unavailable.
  }
}

useAutoRefresh(refreshOverview, 30000)

onMounted(refreshOverview)

async function handleLogout() {
  await authStore.logout()
  await router.replace('/login')
}
</script>
