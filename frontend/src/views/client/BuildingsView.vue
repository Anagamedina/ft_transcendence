<!--
  CLIENT BUILDINGS VIEW (F8, home redesigned in F24)
  Client home page. Without a building open ("Mis edificios", F24):
    - Banner: pending alerts (red); nothing pending but a sensor still out
      of range or offline (amber, e.g. its alert is "En curso"); or
      "Todo en orden" (green). Link to Alertas when there is something.
    - KPIs: buildings, and "Sensores conectados" as "X de Y" (same as the
      building page). It counts the same sensor list as the cards and the
      banner, so all of them change at the same refresh (F30).
    - One BuildingCard per building, most worrying first: offline sensor >
      out of range > smallest margin (utils/pressure.js). Each card shows the
      sensor to watch with its pressure in words and a 7-day sparkline.
  A card opens the building page /app/edificios/:id (F25). Old links with
  ?site=<id> are sent there. Data reloads every minute and when the tab is
  visible again (useAutoRefresh). The trial banner is in ClientLayout (TrialBanner).
  Detailed alerts are in /app/alerts (F9-C).
-->

<template>
  <div class="mx-auto max-w-7xl space-y-6">
    <header class="flex flex-wrap items-end justify-between gap-3">
      <div class="min-w-0">
        <h1 class="text-2xl font-bold text-slate-900">Mis edificios</h1>
        <p class="mt-1 text-sm text-slate-600">
          Lo más urgente primero: de un vistazo sabrás si algo necesita tu
          atención.
        </p>
      </div>
    </header>

    <!-- Banner: what needs attention (home only) -->
    <section
      v-if="pendingTotal !== null"
      class="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-white p-4"
      :class="
        bannerTone === 'success'
          ? 'border-slate-200'
          : toneClasses(bannerTone).border
      "
      aria-live="polite"
    >
      <div class="flex min-w-0 items-center gap-3">
        <span
          class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full p-2"
          :class="toneClasses(bannerTone).pill"
          aria-hidden="true"
        >
          <AppIcon :name="bannerTone === 'success' ? 'droplet' : 'alert'" />
        </span>
        <div class="min-w-0">
          <p class="font-semibold text-slate-900">{{ bannerTitle }}</p>
          <p class="text-sm text-slate-700">{{ bannerText }}</p>
        </div>
      </div>
      <RouterLink
        v-if="pendingTotal > 0 || inProgressTotal > 0"
        :to="pendingTotal > 0 ? '/app/alerts' : '/app/alerts?tab=en-curso'"
        class="rounded-lg bg-aqua-600 px-4 py-2 text-sm font-semibold text-white hover:bg-aqua-700"
      >
        Ver alertas
      </RouterLink>
    </section>

    <!-- KPIs (home only) -->
    <section
      aria-label="Indicadores"
      class="grid grid-cols-1 gap-4 sm:grid-cols-2"
    >
      <KPICard
        v-for="kpi in kpis"
        :key="kpi.label"
        :label="kpi.label"
        :value="kpi.value"
      >
        <template #icon><AppIcon :name="kpi.icon" /></template>
      </KPICard>
    </section>

    <LoadingState v-if="sitesLoading" message="Cargando tus edificios…" />
    <ErrorState
      v-else-if="sitesError"
      :message="sitesError"
      @retry="loadSites"
    />
    <EmptyState
      v-else-if="!sites.length"
      icon="building"
      title="Todavía no tienes edificios"
      message="Cuando AquaGuard dé de alta tu edificio, aparecerá aquí."
    />

    <!-- Building cards, most worrying first -->
    <section
      v-else
      aria-label="Edificios"
      class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3"
    >
      <BuildingCard
        v-for="item in sortedSites"
        :key="item.id"
        :site="item"
        :sensors="sensorsOf(item.id)"
        :points="seriesFor(item.id)"
        :loading-points="seriesLoadingFor(item.id)"
        :pending="pendingBySite[item.id] ?? 0"
        :in-progress="inProgressBySite[item.id] ?? 0"
        @open="openSite"
      />
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import AppIcon from "../../components/AppIcon.vue";
import KPICard from "../../components/KPICard.vue";
import BuildingCard from "../../components/BuildingCard.vue";
import LoadingState from "../../components/LoadingState.vue";
import ErrorState from "../../components/ErrorState.vue";
import EmptyState from "../../components/EmptyState.vue";

import { useSitesStore } from "../../stores/sites.js";
import { useSensorsStore } from "../../stores/sensors.js";
import { useOverviewStore } from "../../stores/overview.js";
import readingService from "../../services/reading.service.js";
import { useAutoRefresh } from "../../composables/useAutoRefresh";
import { useLabels } from "../../composables/useLabels";
import alertsService from "../../services/alerts.service.js";
import {
  compareSensorRisk,
  pressureState,
  worstSensor,
} from "../../utils/pressure.js";

// Same pace as the admin dashboard and ClientLayout (F30)
const REFRESH_MS = 30 * 1000;

const route = useRoute();
const router = useRouter();
const sitesStore = useSitesStore();
const sensorsStore = useSensorsStore();
const overviewStore = useOverviewStore();
const { toneClasses } = useLabels();

// ---------------------------------------------------------------------------
// KPIs. ClientLayout already loads and refreshes the overview (B9).
// "Sensores conectados" is counted from sensorsStore, the same list as the
// cards and the banner: one source, one refresh, no mismatch (F30).
// ---------------------------------------------------------------------------
const kpis = computed(() => {
  const o = overviewStore.overview;
  const all = sensorsStore.sensors;
  const loaded = sensorsStore.status === "success" || all.length > 0;
  const connected = all.filter(
    (sensor) => pressureState(sensor).key !== "offline",
  ).length;
  return [
    { label: "Edificios", icon: "building", value: o?.sites_total ?? "—" },
    {
      // Same wording as the building page and the admin dashboard
      label: "Sensores conectados",
      icon: "wifi",
      value: loaded ? `${connected} de ${all.length}` : "—",
    },
  ];
});

// ---------------------------------------------------------------------------
// Buildings and sensors. A refresh keeps the data on screen: "loading" only
// shows the spinner the first time.
// ---------------------------------------------------------------------------
const sites = computed(() => sitesStore.sites);
const sitesLoading = computed(
  () => ["idle", "loading"].includes(sitesStore.status) && !sites.value.length,
);
const sitesError = computed(() =>
  sitesStore.status === "error"
    ? sitesStore.error?.message || "No se han podido cargar tus edificios."
    : "",
);
async function loadSites() {
  try {
    await sitesStore.fetchSites();
  } catch {
    // The store exposes the error state to the view
  }
}

async function loadSensors() {
  try {
    await sensorsStore.fetchSensors();
  } catch {
    // The store exposes the error state to the view
  }
}

function sensorsOf(id) {
  return sensorsStore.sensors.filter((sensor) => sensor.site_id === id);
}

// Most worrying building first: compares the worst sensor of each one
// (offline > out of range > smallest margin). Buildings without sensors go
// last; ties by pending alerts, then by name.
const sortedSites = computed(() => {
  const worst = new Map(
    sites.value.map((item) => [item.id, worstSensor(sensorsOf(item.id))]),
  );
  return [...sites.value].sort((a, b) => {
    const wa = worst.get(a.id);
    const wb = worst.get(b.id);
    if (!wa || !wb)
      return wa ? -1 : wb ? 1 : a.name.localeCompare(b.name, "es");
    return (
      compareSensorRisk(wa, wb) ||
      (pendingBySite.value[b.id] ?? 0) - (pendingBySite.value[a.id] ?? 0) ||
      a.name.localeCompare(b.name, "es")
    );
  });
});

// ---------------------------------------------------------------------------
// Pending alerts (state ACTIVE) for the banner and the cards, and the count
// of "En curso" for the banner text
// ---------------------------------------------------------------------------
const pendingAlerts = ref([]);
const inProgressAlerts = ref([]);
const pendingTotal = ref(null);
const inProgressTotal = ref(0);

async function loadPending() {
  try {
    const [pending, inProgress] = await Promise.all([
      alertsService.getAlerts({ state: "ACTIVE" }),
      alertsService.getAlerts({ state: "ACKNOWLEDGED" }),
    ]);
    // Filtered again: the mock adapter ignores `state`
    pendingAlerts.value = (pending.data.items ?? []).filter(
      (alert) => alert.state === "ACTIVE",
    );
    inProgressAlerts.value = (inProgress.data.items ?? []).filter(
      (alert) => alert.state === "ACKNOWLEDGED",
    );
    pendingTotal.value = Math.max(
      pending.data.total ?? 0,
      pendingAlerts.value.length,
    );
    inProgressTotal.value = Math.max(
      inProgress.data.total ?? 0,
      inProgressAlerts.value.length,
    );
  } catch {
    // Without the count the banner simply does not appear
  }
}

function countBySite(alerts) {
  const bySite = {};
  for (const alert of alerts)
    bySite[alert.site_id] = (bySite[alert.site_id] ?? 0) + 1;
  return bySite;
}
const pendingBySite = computed(() => countBySite(pendingAlerts.value));
const inProgressBySite = computed(() => countBySite(inProgressAlerts.value));

// Sensors out of range or offline right now, even if their alert is
// already "En curso": the problem is still there
const sensorsWithProblem = computed(
  () =>
    sensorsStore.sensors.filter((sensor) =>
      ["out", "offline"].includes(pressureState(sensor).key),
    ).length,
);

// danger: something pending · warning: nothing pending but a sensor is
// still out of range or offline · success: all fine
const bannerTone = computed(() => {
  if (pendingTotal.value > 0) return "danger";
  if (sensorsWithProblem.value > 0) return "warning";
  return "success";
});

const bannerTitle = computed(() => {
  const n = pendingTotal.value;
  if (n > 0)
    return n === 1
      ? "Tienes 1 aviso sin atender"
      : `Tienes ${n} avisos sin atender`;
  const s = sensorsWithProblem.value;
  if (s > 0)
    return s === 1
      ? "Hay 1 sensor fuera de lo normal"
      : `Hay ${s} sensores fuera de lo normal`;
  // Nothing for the client to do, but the team is still on some alerts
  if (inProgressTotal.value > 0) return "No tienes nada sin atender";
  return "Todo en orden";
});

const bannerText = computed(() => {
  if (pendingTotal.value > 0)
    return "Revísalo y pulsa «Me encargo» cuando te ocupes.";
  const n = inProgressTotal.value;
  if (n > 0)
    return n === 1
      ? "Tu equipo ya está atendiendo 1 aviso. AquaGuard revisará las lecturas para cerrarlo."
      : `Tu equipo ya está atendiendo ${n} avisos. AquaGuard revisará las lecturas para cerrarlo.`;
  if (sensorsWithProblem.value > 0) return "AquaGuard lo sigue vigilando.";
  return "Ningún aviso sin atender. AquaGuard sigue vigilando tus edificios.";
});

// ---------------------------------------------------------------------------
// Sparkline of each card: 7-day series of the sensor to watch (B7)
// ---------------------------------------------------------------------------
const series = ref({}); // sensorId -> points
const seriesLoading = ref({}); // sensorId -> true while loading

function watchedId(id) {
  return worstSensor(sensorsOf(id))?.id ?? null;
}

function seriesFor(id) {
  return series.value[watchedId(id)] ?? [];
}

function seriesLoadingFor(id) {
  return Boolean(seriesLoading.value[watchedId(id)]);
}

async function loadSeries({ silent = false } = {}) {
  const ids = [
    ...new Set(sites.value.map((item) => watchedId(item.id))),
  ].filter(Boolean);
  await Promise.all(
    ids.map(async (sensorId) => {
      if (!silent && !series.value[sensorId])
        seriesLoading.value = { ...seriesLoading.value, [sensorId]: true };
      try {
        const response = await readingService.getSensorSeries(sensorId, {
          days: 7,
        });
        series.value = {
          ...series.value,
          [sensorId]: response.data.points ?? [],
        };
      } catch {
        // The card says "Sin lecturas"; the next refresh tries again
      } finally {
        seriesLoading.value = { ...seriesLoading.value, [sensorId]: false };
      }
    }),
  );
}

// When sensors arrive or another sensor becomes the one to watch.
const watchedKey = computed(() =>
  sites.value.map((item) => watchedId(item.id)).join(","),
);

// Load the sparklines when the sites and sensors arrive. immediate: coming
// back from another page, the stores already have them, so watchedKey does
// not change and `series` is empty.
watch(watchedKey, () => loadSeries(), { immediate: true });

// A card opens the building page (F25)
function openSite(id) {
  router.push({ name: "ClientBuilding", params: { id } });
}

// ---------------------------------------------------------------------------
// Loading and auto refresh (every minute and when the tab is visible again)
// ---------------------------------------------------------------------------
function loadAll() {
  return Promise.all([loadSites(), loadSensors(), loadPending()]);
}

function refresh() {
  return Promise.all([loadAll(), loadSeries({ silent: true })]);
}

useAutoRefresh(refresh, REFRESH_MS);

onMounted(() => {
  // Old links /app?site=<id> go to the building page
  if (route.query.site) {
    router.replace({
      name: "ClientBuilding",
      params: { id: route.query.site },
    });
    return;
  }
  loadAll();
});
</script>
