<!--
  ADMIN DASHBOARD VIEW
  Main admin page: KPIs summary, sites, sensors and alerts overview.
  Rendered inside AdminLayout. Data comes only from Pinia stores (no direct HTTP calls).
-->

<script setup>
import { ref, computed, defineAsyncComponent } from 'vue'
import AdminLayout from '../../layouts/AdminLayout.vue'
import KPICard from '../../components/KPICard.vue'
import AppIcon from '../../components/AppIcon.vue'
import { useSensorsStore } from '../../stores/sensors'
import { useAlertsStore } from '../../stores/alerts'
import SitesSummary from '../../components/SitesSummary.vue'
import SensorsSummary from '../../components/SensorsSummary.vue'
import AlertsSummary from '../../components/AlertsSummary.vue'
import Modal from '../../components/Modal.vue'
// TODO: temporary mock data until the sites store exists (Services/Stores area).
// Replace with the store, e.g. `sitesStore.sites`, and delete this import.
import { sites as mockSites } from '../../services/fixtures/sites'

// Loaded only when the map window is opened (MapLibre is heavy, ~900 KB)
const SitesMap = defineAsyncComponent(() => import('../../components/SitesMap.vue'))

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

// Alert level of each site for the map: an alert belongs to a sensor,
// and a sensor belongs to a site (alert.sensor_id -> sensor.site_id).
// If a site has several active alerts, the most severe one wins.
const ALERT_RANK = { none: 0, warning: 1, critical: 2 }
const sitesForMap = computed(() =>
  mockSites.map((site) => {
    const sensorIds = new Set(
      sensorStore.sensors.filter((s) => s.site_id === site.id).map((s) => s.id)
    )
    let alertLevel = 'none'
    activeAlertList.value
      .filter((a) => sensorIds.has(a.sensor_id))
      .forEach((a) => {
        const level = a.severity === 'CRITICAL' ? 'critical' : 'warning'
        if (ALERT_RANK[level] > ALERT_RANK[alertLevel]) alertLevel = level
      })
    return { ...site, alertLevel }
  })
)

// Compact map card: summary + button that opens the map in a modal window
const showMap = ref(false)
const warningSites = computed(() => sitesForMap.value.filter((s) => s.alertLevel === 'warning').length)
const criticalSites = computed(() => sitesForMap.value.filter((s) => s.alertLevel === 'critical').length)
</script>

<template>
  <AdminLayout>
    <h1 class="text-2xl font-bold text-gray-800 mb-6">Dashboard Admin</h1>

    <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <KPICard label="Sites" :value="mockSites.length">
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
      <SitesSummary :sites="mockSites" />
      <SensorsSummary :sensors="sensorStore.sensors" />
    </section>

    <!-- Map card: compact on the dashboard, full map opens in a modal -->
    <section
      class="bg-white border border-gray-200 rounded-xl shadow-md p-5 mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
    >
      <div class="flex items-center gap-3">
        <span class="w-10 h-10 shrink-0 rounded-full bg-aqua-50 text-aqua-600 flex items-center justify-center p-2.5">
          <AppIcon name="building" />
        </span>
        <div>
          <h2 class="text-lg font-bold text-gray-800">Mapa de sites</h2>
          <p class="text-sm text-gray-500">
            {{ sitesForMap.length }} sites
            <span v-if="criticalSites" class="ml-2 font-semibold text-danger">· {{ criticalSites }} con alerta crítica</span>
            <span v-if="warningSites" class="ml-2 font-semibold text-amber-600">· {{ warningSites }} con aviso</span>
          </p>
        </div>
      </div>

      <button
        class="shrink-0 bg-aqua-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-aqua-800 transition"
        @click="showMap = true"
      >
        Ver mapa
      </button>
    </section>

    <Modal :show="showMap" title="Mapa de sites · Barcelona" size="xl" @close="showMap = false">
      <SitesMap :sites="sitesForMap" height="70vh" />
    </Modal>

    <AlertsSummary :alerts="activeAlertList" />
  </AdminLayout>
</template>