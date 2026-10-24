<!--
  CLIENT BUILDINGS VIEW (F8, home redesigned in F24)
  Client home page. Without a building open ("Mis edificios", F24):
    - Banner: pending alerts (red); nothing pending but a sensor still out
      of range or offline (amber, e.g. its alert is "En curso"); or
      "Todo en orden" (green). Link to Alertas when there is something.
    - KPIs: buildings, and sensors with how many are offline.
    - One BuildingCard per building, most worrying first: offline sensor >
      out of range > smallest margin (utils/pressure.js). Each card shows the
      sensor to watch with its pressure in words and a 7-day sparkline.
    - The open building floor by floor (BuildingStack, F4) and the selected
      sensor with its 7-day pressure chart (SensorDetailPanel + PressureChart,
      F5, series from B7).
    - Alerts of the week by sensor and day (WeekAlertsGrid, B9).
  The open building (/app?site=<id>) stays as it was until the building page
  of F25 replaces it.
  The open building lives in the URL (/app?site=<id>), so reloading and the
  back button keep it. Data reloads every minute and when the tab is visible
  again (useAutoRefresh). The trial banner is in ClientLayout (TrialBanner).
  Detailed alerts are in /app/alerts (F9-C).
-->

<template>
  <div class="mx-auto max-w-7xl space-y-6">
    <header class="flex flex-wrap items-end justify-between gap-3">
      <div class="min-w-0">
        <h1 class="text-2xl font-bold text-slate-900">
          {{ site ? site.name : "Mis edificios" }}
        </h1>
        <p class="mt-1 text-sm text-slate-600">
          {{
            site
              ? siteSummary
              : "Lo más urgente primero: de un vistazo sabrás si algo necesita tu atención."
          }}
        </p>
      </div>
      <button
        v-if="site"
        type="button"
        class="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        @click="openSite(null)"
      >
        ← Todos los edificios
      </button>
    </header>

    <!-- Banner: what needs attention (home only) -->
    <section
      v-if="!site && pendingTotal !== null"
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
      v-if="!site"
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
      v-else-if="!site"
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

    <!-- Open building -->
    <template v-else>
      <LoadingState v-if="sensorsLoading" message="Cargando sensores…" />
      <ErrorState
        v-else-if="sensorsError"
        :message="sensorsError"
        @retry="loadSensors"
      />

      <div
        v-else
        class="grid grid-cols-1 items-start gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]"
      >
        <BuildingStack
          :name="site.name"
          :floors="site.floors"
          :basements="site.basements"
          :sensors="siteSensors"
          :selected-id="selectedId"
          @select="selectSensor"
        />

        <div ref="sidePanel">
          <SensorDetailPanel
            v-if="selectedSensor"
            :sensor="selectedSensor"
            :readings="readings"
            :alert-count="alertCount"
            :loading="readingsLoading"
            :error="readingsError"
            @retry="loadReadings()"
          />
          <EmptyState
            v-else-if="siteSensors.length"
            icon="droplet"
            title="Elige un sensor"
            message="Toca un sensor del edificio para ver su gráfica de los últimos 7 días."
            compact
          />
        </div>
      </div>

      <section
        class="rounded-xl border border-slate-200 bg-white p-5"
        aria-labelledby="week-alerts-title"
      >
        <div class="mb-3 flex flex-wrap items-baseline justify-between gap-2">
          <h2 id="week-alerts-title" class="text-lg font-bold text-slate-900">
            Alertas de la semana
          </h2>
          <RouterLink
            to="/app/alerts"
            class="text-sm font-medium text-aqua-700 hover:underline"
          >
            Ver todas las alertas
          </RouterLink>
        </div>
        <LoadingState
          v-if="weeklyLoading"
          message="Cargando alertas de la semana…"
          compact
        />
        <ErrorState
          v-else-if="weeklyError"
          :message="weeklyError"
          compact
          @retry="loadWeekly()"
        />
        <WeekAlertsGrid
          v-else-if="weekly"
          :days="weekly.days"
          :rows="weekly.rows"
          :site-name="site.name"
          :selected-id="selectedId"
          @select="selectSensor"
        />
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import AppIcon from "../../components/AppIcon.vue";
import KPICard from "../../components/KPICard.vue";
import BuildingCard from "../../components/BuildingCard.vue";
import BuildingStack from "../../components/BuildingStack.vue";
import SensorDetailPanel from "../../components/SensorDetailPanel.vue";
import WeekAlertsGrid from "../../components/WeekAlertsGrid.vue";
import LoadingState from "../../components/LoadingState.vue";
import ErrorState from "../../components/ErrorState.vue";
import EmptyState from "../../components/EmptyState.vue";

import { useSitesStore } from "../../stores/sites.js";
import { useSensorsStore } from "../../stores/sensors.js";
import { useAlertsStore } from "../../stores/alerts.js";
import { useOverviewStore } from "../../stores/overview.js";
import readingService from "../../services/reading.service.js";
import analyticsService from "../../services/analytics.service.js";
import { useAutoRefresh } from "../../composables/useAutoRefresh";
import { useLabels } from "../../composables/useLabels";
import alertsService from "../../services/alerts.service.js";
import {
  compareSensorRisk,
  pressureState,
  worstSensor,
} from "../../utils/pressure.js";

const REFRESH_MS = 60 * 1000;
const DAY_MS = 24 * 60 * 60 * 1000;

const route = useRoute();
const router = useRouter();
const sitesStore = useSitesStore();
const sensorsStore = useSensorsStore();
const alertsStore = useAlertsStore();
const overviewStore = useOverviewStore();
const { toneClasses } = useLabels();

// ---------------------------------------------------------------------------
// KPIs. ClientLayout already loads and refreshes the overview (B9).
// ---------------------------------------------------------------------------
const kpis = computed(() => {
  const o = overviewStore.overview;
  const offline = o ? o.sensors_total - o.sensors_online : 0;
  return [
    { label: "Edificios", icon: "building", value: o?.sites_total ?? "—" },
    {
      label: "Sensores",
      icon: "wifi",
      value: o
        ? offline > 0
          ? `${o.sensors_total} · ${offline} sin conexión`
          : `${o.sensors_total} · todos conectados`
        : "—",
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
const sensorsLoading = computed(
  () =>
    ["idle", "loading"].includes(sensorsStore.status) &&
    !sensorsStore.sensors.length,
);
const sensorsError = computed(() =>
  sensorsStore.status === "error"
    ? sensorsStore.error?.message || "No se han podido cargar los sensores."
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

async function loadAlerts() {
  try {
    await alertsStore.fetchAlerts();
  } catch {
    // Only the "alerts in 7 days" figure depends on it: it shows '—'
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
      ? "Tienes 1 aviso pendiente"
      : `Tienes ${n} avisos pendientes`;
  const s = sensorsWithProblem.value;
  if (s > 0)
    return s === 1
      ? "Hay 1 sensor fuera de lo normal"
      : `Hay ${s} sensores fuera de lo normal`;
  // Nothing for the client to do, but the team is still on some alerts
  if (inProgressTotal.value > 0) return "No tienes nada pendiente";
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
  return "Ningún aviso pendiente. AquaGuard sigue vigilando tus edificios.";
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

// ---------------------------------------------------------------------------
// Open building: the one in the URL, or the only one when there is just one
// ---------------------------------------------------------------------------
const siteId = computed(() => {
  const fromUrl = route.query.site;
  if (fromUrl && sitesStore.siteById(fromUrl)) return fromUrl;
  // F24: the home always shows the summary, even with a single building
  return null;
});

const site = computed(() =>
  siteId.value ? sitesStore.siteById(siteId.value) : null,
);

// Also when coming back to the home from an open building
// ("← Todos los edificios"): the cards were not on screen meanwhile.
// immediate: coming back from another page, the stores already have the
// sites and sensors, so watchedKey does not change and `series` is empty
watch(
  [watchedKey, siteId],
  () => {
    if (!siteId.value) loadSeries();
  },
  { immediate: true },
);

function openSite(id) {
  const query = { ...route.query };
  if (id) query.site = id;
  else delete query.site;
  router.push({ query });
}

const siteSensors = computed(() =>
  sensorsStore.sensors.filter((sensor) => sensor.site_id === siteId.value),
);

// "Av. Diagonal 19 · 4 plantas + 2 sótanos · 8 sensores"
const siteSummary = computed(() => {
  const s = site.value;
  const parts = [];
  if (s.address) parts.push(s.address);
  parts.push(
    `${s.floors} ${s.floors === 1 ? "planta" : "plantas"}` +
      (s.basements > 0
        ? ` + ${s.basements} ${s.basements === 1 ? "sótano" : "sótanos"}`
        : ""),
  );
  parts.push(
    `${siteSensors.value.length} ${siteSensors.value.length === 1 ? "sensor" : "sensores"}`,
  );
  return parts.join(" · ");
});

// ---------------------------------------------------------------------------
// Selected sensor and its 7-day series (B7)
// ---------------------------------------------------------------------------
const selectedId = ref(null);
const sidePanel = ref(null);
const selectedSensor = computed(
  () =>
    siteSensors.value.find((sensor) => sensor.id === selectedId.value) ?? null,
);

function selectSensor(id) {
  selectedId.value = id;
  // On small screens the panel is below the building: bring it into view
  nextTick(() => {
    if (window.matchMedia?.("(max-width: 1023px)").matches) {
      sidePanel.value?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
}

// When a building opens, show its most worrying sensor straight away
const HEALTH_ORDER = { CRITICAL: 0, WARNING: 1, OFFLINE: 2, OK: 3 };
function defaultSensorId() {
  const [first] = [...siteSensors.value].sort(
    (a, b) => (HEALTH_ORDER[a.health] ?? 4) - (HEALTH_ORDER[b.health] ?? 4),
  );
  return first?.id ?? null;
}

const readings = ref([]);
const readingsLoading = ref(false);
const readingsError = ref("");

// silent: refresh without the spinner, keeping the chart if it fails
async function loadReadings({ silent = false } = {}) {
  const sensorId = selectedId.value;
  if (!sensorId) return;
  if (!silent) {
    readingsLoading.value = true;
    readingsError.value = "";
    readings.value = [];
  }
  try {
    const response = await readingService.getSensorSeries(sensorId, {
      days: 7,
    });
    if (selectedId.value !== sensorId) return;
    // PressureChart takes ReadingResponse-like points: the bucket average
    readings.value = (response.data.points ?? []).map((point) => ({
      pressure: point.avg,
      measured_at: point.t,
    }));
    readingsError.value = "";
  } catch (err) {
    if (selectedId.value !== sensorId || silent) return;
    readingsError.value =
      err?.message || "No se han podido cargar las lecturas.";
  } finally {
    if (selectedId.value === sensorId) readingsLoading.value = false;
  }
}

watch(selectedId, () => loadReadings());

// Alerts of the selected sensor in the last 7 days
const alertCount = computed(() => {
  // During a refresh the previous list is still valid
  const ready =
    alertsStore.status === "success" ||
    (alertsStore.status === "loading" && alertsStore.alerts.length);
  if (!selectedId.value || !ready) return null;
  const since = Date.now() - 7 * DAY_MS;
  return alertsStore.alerts.filter(
    (alert) =>
      alert.sensor_id === selectedId.value &&
      new Date(alert.created_at).getTime() >= since,
  ).length;
});

// ---------------------------------------------------------------------------
// Alerts of the week (B9)
// ---------------------------------------------------------------------------
const weekly = ref(null);
const weeklyLoading = ref(false);
const weeklyError = ref("");

async function loadWeekly({ silent = false } = {}) {
  const id = siteId.value;
  if (!id) return;
  if (!silent) {
    weeklyLoading.value = true;
    weeklyError.value = "";
    weekly.value = null;
  }
  try {
    const response = await analyticsService.getWeeklyAlerts({ site_id: id });
    if (siteId.value !== id) return;
    weekly.value = response.data;
    weeklyError.value = "";
  } catch (err) {
    if (siteId.value !== id || silent) return;
    weeklyError.value =
      err?.message || "No se han podido cargar las alertas de la semana.";
  } finally {
    if (siteId.value === id) weeklyLoading.value = false;
  }
}

// Another building (or the first load): reset the sensor and load its week
watch(
  siteId,
  (id) => {
    selectedId.value = null;
    weekly.value = null;
    if (!id) return;
    loadWeekly();
  },
  { immediate: true },
);

// Pick the default sensor once the building and its sensors are known
watch(
  () => [siteId.value, siteSensors.value.length],
  () => {
    if (siteId.value && !selectedSensor.value)
      selectedId.value = defaultSensorId();
  },
  { immediate: true },
);

// ---------------------------------------------------------------------------
// Loading and auto refresh (every minute and when the tab is visible again)
// ---------------------------------------------------------------------------
function loadAll() {
  return Promise.all([loadSites(), loadSensors(), loadAlerts(), loadPending()]);
}

function refresh() {
  return Promise.all([
    loadAll(),
    loadWeekly({ silent: true }),
    loadReadings({ silent: true }),
    siteId.value ? null : loadSeries({ silent: true }),
  ]);
}

useAutoRefresh(refresh, REFRESH_MS);

onMounted(loadAll);
</script>
