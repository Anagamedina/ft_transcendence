<!-- CLIENT DASHBOARD — sensores propios, histórico Chart.js, alertas. -->

<template>
  <div>
    <button
      type="button"
      @click="handleLogout"
      :disabled="authStore.status === 'loading'"
    >
      {{ authStore.status === 'loading'
        ? 'Login out...'
        : 'Logout'
      }}
    </button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useSensorsStore } from '../../stores/sensors'
import { useAlertsStore } from '../../stores/alerts'

const router = useRouter()

const authStore = useAuthStore()
const sensorStore = useSensorsStore()
const alertsStore = useAlertsStore()

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>