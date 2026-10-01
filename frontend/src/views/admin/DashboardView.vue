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
import SensorsSummary from '../../components/SensorsSummary.vue'
import AlertsSummary from '../../components/AlertsSummary.vue'
import SitesMap from '../../components/SitesMap.vue'
// TODO: temporary mock data until the sites store exists (Services/Stores area).
// Replace with the store, e.g. `sitesStore.sites`, and delete this import.
import { sites as mockSites } from '../../services/fixtures/sites'

const sensorStore = useSensorsStore()
const alertsStore = useAlertsStore()

const totalSensors = computed(() => sensorStore.sensorCount)
const onlineSensors = computed(
  () => sensorStore.sensors.filter((s) => s.status === 'ONLINE').length
)
const activeAlertList = computed(
  () => alertsStore.alerts.filter((a) => a.status === 'ACTIVE')
)
const activeAlerts = computed(() => activeAlertList.value.length)
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

    <section class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8">
      <SitesSummary />
      <SensorsSummary :sensors="sensorStore.sensors" />
    </section>

    <section class="mb-8">
      <SitesMap :sites="mockSites" />
    </section>

    <AlertsSummary :alerts="activeAlertList" />
  </AdminLayout>
</template>