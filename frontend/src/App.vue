<template>
  <div id="app">
    <h1>✅ AquaGuard Frontend funcionando</h1>
    <p>this is a test to check the user is: {{ authStore.isAdmin}} and his role is {{ authStore.role }}</p>
    <router-view />
  </div>
</template>

<script setup>
import { useAuthStore } from './stores/auth'
import { useSensorsStore } from './stores/sensors'
import { useAlertsStore } from './stores/alerts'

const authStore = useAuthStore()
const sensorStore = useSensorsStore()
const alertsStore = useAlertsStore()


</script>

<style>
body {
  margin: 0;
  padding: 0;
}

#app {
  min-height: 100vh;
}
</style>
