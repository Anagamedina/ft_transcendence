<!--
  ADMIN DASHBOARD VIEW
  Main admin page: KPIs summary, sites, sensors and alerts overview.
  Rendered inside AdminLayout. Data comes only from Pinia stores (no direct HTTP calls).
  KPIs, sites, sensors and alerts are fetched on mount; loading / error / empty states are shown
  inside each summary card, and retry re-runs the store action.
-->

<script setup>
import { ref, computed, onMounted, defineAsyncComponent } from "vue";
import AdminLayout from "../../layouts/AdminLayout.vue";
import KPICard from "../../components/KPICard.vue";
import AppIcon from "../../components/AppIcon.vue";
import ErrorState from "../../components/ErrorState.vue";
import { useSensorsStore } from "../../stores/sensors";
import { useAlertsStore } from "../../stores/alerts";
import { useSitesStore } from "../../stores/sites";
import { useOverviewStore } from "../../stores/overview";
import SitesSummary from "../../components/SitesSummary.vue";
import SensorsSummary from "../../components/SensorsSummary.vue";
import AlertsSummary from "../../components/AlertsSummary.vue";
import Modal from "../../components/Modal.vue";
import AnalyticsPanel from "../../components/AnalyticsPanel.vue";

// Loaded only when the map window is opened (MapLibre is heavy, ~900 KB)
const SitesMap = defineAsyncComponent(
  () => import("../../components/SitesMap.vue"),
);

const sensorStore = useSensorsStore();
const alertsStore = useAlertsStore();
const sitesStore = useSitesStore();
const overviewStore = useOverviewStore();

// Load data on mount. Errors are already stored in each store (status/error),
// so we only catch them here to avoid unhandled promise rejections.
async function loadSensors() {
  try {
    await sensorStore.fetchSensors();
  } catch {
    /* handled via sensorStore.error */
  }
}
async function loadAlerts() {
  try {
    await alertsStore.fetchAlerts();
  } catch {
    /* handled via alertsStore.error */
  }
}
async function loadSites() {
  try {
    await sitesStore.fetchSites();
  } catch {
    /* handled via sitesStore.error */
  }
}
async function loadOverview() {
  try {
    await overviewStore.fetchOverview();
  } catch {
    /* handled via overviewStore.error */
  }
}

onMounted(() => {
  loadOverview();
  loadSites();
  loadSensors();
  loadAlerts();
});

// KPIs come from GET /api/analytics/overview. They show "—" until the API
// answers, so "0" always means a real zero.
const kpis = computed(() => {
  const data = overviewStore.overview;
  if (!data) {
    return { clients: "—", sensors: "—", alerts: "—", resolution: "—" };
  }
  return {
    clients: `${data.organizations_needing_attention} de ${data.organizations_total}`,
    sensors: `${data.sensors_online} de ${data.sensors_total}`,
    alerts: data.open_alerts,
    resolution: formatMinutes(data.median_resolution_minutes),
  };
});

// null = no alert was resolved in the last 30 days
function formatMinutes(minutes) {
  if (minutes === null) return "—";
  const total = Math.round(minutes);
  if (total < 60) return `${total} min`;
  return `${Math.floor(total / 60)} h ${total % 60} min`;
}

const activeAlertList = computed(() =>
  alertsStore.alerts.filter((a) => a.status === "ACTIVE"),
);

// The API already sends the status of each site, computed from its open alerts.
// The map only needs it with the names of its own marker levels.
const ALERT_LEVELS = { OK: "none", WARNING: "warning", CRITICAL: "critical" };
const sitesForMap = computed(() =>
  sitesStore.sites.map((site) => ({
    ...site,
    alertLevel: ALERT_LEVELS[site.status] ?? "none",
  })),
);

// Compact map card: summary + button that opens the map in a modal window
const showMap = ref(false);
const warningSites = computed(
  () => sitesForMap.value.filter((s) => s.alertLevel === "warning").length,
);
const criticalSites = computed(
  () => sitesForMap.value.filter((s) => s.alertLevel === "critical").length,
);
</script>

<template>
  <AdminLayout>
    <h1 class="text-2xl font-bold text-gray-800 mb-6">Panel</h1>

    <ErrorState
      v-if="overviewStore.status === 'error'"
      class="mb-4"
      compact
      title="No se han podido cargar los indicadores"
      :message="overviewStore.error?.message"
      @retry="loadOverview"
    />

    <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <KPICard label="Clientes que necesitan atención" :value="kpis.clients">
        <template #icon><AppIcon name="users" /></template>
      </KPICard>

      <KPICard label="Sensores en línea" :value="kpis.sensors">
        <template #icon><AppIcon name="wifi" /></template>
      </KPICard>

      <KPICard label="Alertas abiertas" :value="kpis.alerts">
        <template #icon><AppIcon name="alert" /></template>
      </KPICard>

      <KPICard label="Tiempo de resolución" :value="kpis.resolution">
        <template #icon><AppIcon name="bar-chart" /></template>
      </KPICard>
    </section>

    

    <!-- F19: charts, date range, CSV export and auto refresh -->
    <AnalyticsPanel />

    <!-- Map card: compact on the dashboard, full map opens in a modal -->
<section
  class="bg-white border border-gray-200 rounded-xl shadow-md p-5 mb-8"
>
  <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
    <div>
      <div class="flex items-center gap-2 mb-1">
        <AppIcon
          name="building"
          class="text-aqua-700"
          style="width: 20px; height: 20px; flex: 0 0 20px;"
        />

        <h2 class="text-lg font-bold text-gray-800">
          Mapa de edificios
        </h2>
      </div>

      <p class="text-sm text-gray-500">
        {{ sitesForMap.length }}
        {{ sitesForMap.length === 1 ? "edificio" : "edificios" }}

        <span
          v-if="criticalSites"
          class="ml-2 font-semibold text-red-700"
        >
          · {{ criticalSites }} con alerta crítica
        </span>

        <span
          v-if="warningSites"
          class="ml-2 font-semibold text-amber-700"
        >
          · {{ warningSites }} con aviso
        </span>
      </p>
    </div>

    <router-link
      to="/admin/sites"
      class="text-sm font-semibold text-aqua-700 hover:text-aqua-900 underline"
    >
      Ver edificios
    </router-link>
  </div>

  <SitesMap
    :sites="sitesForMap"
    height="400px"
  />
</section>

    <AlertsSummary
      :alerts="activeAlertList"
      :status="alertsStore.status"
      :error="alertsStore.error"
      @retry="loadAlerts"
    />

  </AdminLayout>
</template>
