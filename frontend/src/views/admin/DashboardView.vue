<!--
  ADMIN DASHBOARD VIEW
  Main admin page: KPIs summary, sites, sensors and alerts overview.
  Rendered inside AdminLayout. Data comes only from Pinia stores (no direct HTTP calls).
-->

<script setup>
import { computed } from 'vue'
import AdminLayout from '../../layouts/AdminLayout.vue'
import KPICard from '../../components/KPICard.vue'
import AppIcon from '../../components/AppIcon.vue'
import { useSensorsStore } from '../../stores/sensors'
import { useAlertsStore } from '../../stores/alerts'
import SitesSummary from '../../components/SitesSummary.vue'

const sensorStore = useSensorsStore()
const alertsStore = useAlertsStore()

const totalSensors = computed(() => sensorStore.sensorCount)
const onlineSensors = computed(
  () => sensorStore.sensors.filter((s) => s.status === 'ONLINE').length
)
const activeAlerts = computed(
  () => alertsStore.alerts.filter((a) => a.status === 'ACTIVE').length
)
</script>

<template>
  <AdminLayout>
    <h1 class="text-2xl font-bold text-gray-800 mb-6">Dashboard Admin</h1>

    <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <KPICard label="Sites">
        <template #icon><AppIcon name="building" /></template>
      </KPICard>

      <KPICard label="Sensores totales" :value="totalSensors">
        <template #icon><AppIcon name="droplet" /></template>
      </KPICard>

      <KPICard label="Sensores online" :value="onlineSensors">
        <template #icon><AppIcon name="wifi" /></template>
      </KPICard>

      <KPICard label="Alertas activas" :value="activeAlerts">
        <template #icon><AppIcon name="alert" /></template>
      </KPICard>
    </section>
      <SitesSummary />
  </AdminLayout>
</template>