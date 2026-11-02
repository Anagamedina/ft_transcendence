<!--
  CLIENT BUILDING PAGE (F25)
  /app/edificios/:id — one building. The side menu is the general view (all
  buildings); this page and its tabs are only this building.
    - Header: name, address, floors and sensors.
    - Three indicators, each a link: Sin atender, En curso (to the Alertas
      tab) and Sensores conectados as "X de Y" (to Plantas y sensores).
    - Tabs (?tab=): Vista general (default) · Plantas y sensores (plantas) ·
      Alertas (alertas) · Documentos (documentos, F27).
  Vista general:
    - AlertSpotlight: the most important open alert (pending first), with
      "Me encargo" and "Ver gráfico". All fine: a short green message.
    - Tu edificio: BuildingDrawing (roof, floors, street line, basements),
      by alert and pressure state, the same rule as "Mis edificios"; a floor
      with sensors opens Plantas y sensores on that floor.
    - Tu semana: WeekStateGrid (sensor x day, by state) and the week's alerts.
  Plantas y sensores: BuildingFloorsPanel (F26 redesigns it).
  Alertas: ClientAlertsPanel fixed to this building (state in ?estado=).
  Documentos: DocumentsPanel fixed to this building (upload set to it).
  A building that is not the client's (or does not exist): message and the
  way back. Data: GET /api/alerts of this building per state, every 30 s.
  No backend changes.
-->

<template>
  <div class="mx-auto max-w-7xl space-y-6">
    <RouterLink
      to="/app"
      class="inline-flex items-center gap-1 text-sm font-medium text-aqua-700 hover:underline"
    >
      ‹ Mis edificios
    </RouterLink>

    <LoadingState v-if="siteLoading" message="Cargando el edificio…" />
    <ErrorState
      v-else-if="sitesError"
      :message="sitesError"
      @retry="loadSites"
    />
    <EmptyState
      v-else-if="!site"
      icon="building"
      title="No encontramos este edificio"
      message="Puede que no sea de tu organización o que ya no exista."
    >
      <template #action>
        <RouterLink
          to="/app"
          class="rounded-lg bg-aqua-600 px-4 py-2 text-sm font-semibold text-white hover:bg-aqua-700"
        >
          Volver a Mis edificios
        </RouterLink>
      </template>
    </EmptyState>

    <template v-else>
      <header>
        <h1 class="text-3xl font-bold text-slate-900">{{ site.name }}</h1>
        <p class="mt-1 text-sm text-slate-600">{{ siteSummary }}</p>
      </header>

      <!-- Indicators, each one a shortcut -->
      <section
        aria-label="Resumen del edificio"
        class="grid grid-cols-3 gap-2 sm:gap-4"
      >
        <RouterLink
          v-for="item in indicators"
          :key="item.label"
          :to="item.to"
          class="rounded-xl border border-slate-200 bg-white px-3 py-3 hover:border-aqua-400 sm:px-5 sm:py-4 focus-visible:outline focus-visible:outline-2 focus-visible:outline-aqua-600"
        >
          <span
            class="block text-xs font-medium sm:text-sm"
            :class="item.labelClass"
            >{{ item.label }} →</span
          >
          <span
            class="block text-2xl font-bold tabular-nums sm:text-3xl"
            :class="item.valueClass"
            >{{ item.value }}</span
          >
        </RouterLink>
      </section>

      <!-- Tabs of this building -->
      <div
        class="flex items-end gap-1 overflow-x-auto border-b border-slate-200"
      >
        <div
          role="tablist"
          aria-label="Secciones del edificio"
          class="flex shrink-0 gap-1"
        >
          <button
            v-for="(tab, index) in TABS"
            :id="`building-tab-${tab.key}`"
            :key="tab.key"
            ref="tabButtons"
            type="button"
            role="tab"
            :aria-selected="tab.key === activeTab"
            :aria-controls="`building-panel-${tab.key}`"
            :tabindex="tab.key === activeTab ? 0 : -1"
            class="-mb-px whitespace-nowrap border-b-[3px] px-3 py-3 text-sm sm:px-4 sm:text-base"
            :class="
              tab.key === activeTab
                ? 'border-aqua-600 font-semibold text-aqua-700'
                : 'border-transparent text-slate-700 hover:text-aqua-700'
            "
            @click="setTab(tab.key)"
            @keydown.right.prevent="focusTab(index + 1)"
            @keydown.left.prevent="focusTab(index - 1)"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>

      <section
        :id="`building-panel-${activeTab}`"
        role="tabpanel"
        :aria-labelledby="`building-tab-${activeTab}`"
      >
        <!-- Vista general -->
        <div v-if="activeTab === 'general'" class="space-y-6">
          <div
            v-if="actionError"
            class="rounded-lg border border-danger-light bg-danger-light p-3 text-sm text-danger-dark"
            role="alert"
          >
            {{ actionError }}
          </div>

          <LoadingState
            v-if="!alertsLoaded && !alertsError"
            message="Cargando avisos…"
            compact
          />
          <ErrorState
            v-else-if="alertsError"
            :message="alertsError"
            compact
            @retry="loadAlerts()"
          />
          <template v-else>
            <AlertSpotlight
              v-if="spotlight"
              :alert="spotlight"
              :busy="busyAlertId === spotlight.id"
              @acknowledge="acknowledge"
              @chart="openFloor"
            />
            <p v-if="openAlerts.length > 1" class="text-sm text-slate-700">
              Hay {{ openAlerts.length - 1 }}
              {{ openAlerts.length === 2 ? "aviso más" : "avisos más" }} en este
              edificio.
              <RouterLink
                :to="{ query: { tab: 'alertas' } }"
                class="font-medium text-aqua-700 underline hover:text-aqua-900"
                >Ver alertas</RouterLink
              >
            </p>
            <div
              v-if="!spotlight"
              class="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white px-6 py-5"
            >
              <span
                class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full p-2.5"
                :class="toneClasses('success').pill"
                aria-hidden="true"
                ><AppIcon name="droplet"
              /></span>
              <div>
                <p class="font-semibold text-slate-900">
                  Todo en orden en este edificio
                </p>
                <p class="text-sm text-slate-700">
                  No hay avisos abiertos. AquaGuard sigue vigilando.
                </p>
              </div>
            </div>
          </template>

          <div class="flex flex-wrap items-start gap-4">
            <!-- Tu edificio -->
            <section
              aria-labelledby="drawing-title"
              class="flex-[1_1_300px] space-y-3 rounded-2xl border border-slate-200 bg-white p-5 lg:max-w-[380px]"
            >
              <h2 id="drawing-title" class="text-lg font-bold text-slate-900">
                Tu edificio
              </h2>
              <BuildingDrawing
                :name="site.name"
                :floors="site.floors"
                :basements="site.basements"
                :states="floorStates"
                :sensors="siteSensors"
                @select="openFloor"
              />
              <p class="text-center text-xs text-slate-600">
                Pulsa una planta con sensores para verlos
              </p>
            </section>

            <!-- Tu semana -->
            <section
              aria-labelledby="week-title"
              class="min-w-0 flex-[999_1_420px] space-y-3 rounded-2xl border border-slate-200 bg-white p-5"
            >
              <div class="flex flex-wrap items-baseline justify-between gap-2">
                <h2 id="week-title" class="text-lg font-bold text-slate-900">
                  Tu semana
                </h2>
                <RouterLink
                  :to="{ query: { tab: 'alertas' } }"
                  class="text-sm font-medium text-aqua-700 hover:underline"
                >
                  Ver todas las alertas
                </RouterLink>
              </div>
              <WeekStateGrid :sensors="siteSensors" :alerts="allAlerts" />
            </section>
          </div>
        </div>

        <!-- Plantas y sensores -->
        <BuildingFloorsPanel
          v-else-if="activeTab === 'plantas'"
          :site="site"
          :sensors="siteSensors"
          :alerts="allAlerts"
          :focus-floor="focusFloor"
        />

        <!-- Alertas of this building -->
        <ClientAlertsPanel
          v-else-if="activeTab === 'alertas'"
          :fixed-site-id="site.id"
          state-key="estado"
        />

        <!-- Documentos of this building -->
        <DocumentsPanel v-else :site="site" />
      </section>

      <!-- Announces "Me encargo" to screen readers -->
      <p class="sr-only" aria-live="polite">{{ liveMessage }}</p>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import AppIcon from "../../components/AppIcon.vue";
import AlertSpotlight from "../../components/AlertSpotlight.vue";
import BuildingDrawing from "../../components/BuildingDrawing.vue";
import WeekStateGrid from "../../components/WeekStateGrid.vue";
import BuildingFloorsPanel from "../../components/BuildingFloorsPanel.vue";
import ClientAlertsPanel from "../../components/ClientAlertsPanel.vue";
import DocumentsPanel from "../../components/DocumentsPanel.vue";
import LoadingState from "../../components/LoadingState.vue";
import ErrorState from "../../components/ErrorState.vue";
import EmptyState from "../../components/EmptyState.vue";

import alertsService from "../../services/alerts.service.js";
import { useSitesStore } from "../../stores/sites.js";
import { useSensorsStore } from "../../stores/sensors.js";
import { useOverviewStore } from "../../stores/overview.js";
import { useLabels } from "../../composables/useLabels";
import { REFRESH_MS, useAutoRefresh } from "../../composables/useAutoRefresh";
import { apiErrorMessage } from "../../utils/apiError.js";
import { pressureState } from "../../utils/pressure.js";

const TABS = [
  { key: "general", label: "Vista general" },
  { key: "plantas", label: "Plantas y sensores" },
  { key: "alertas", label: "Alertas" },
  { key: "documentos", label: "Documentos" },
];

const route = useRoute();
const router = useRouter();
const sitesStore = useSitesStore();
const sensorsStore = useSensorsStore();
const overviewStore = useOverviewStore();
const { toneClasses } = useLabels();

// ---------------------------------------------------------------------------
// Tabs in the URL (?tab=plantas | alertas | documentos) and the floor asked for
// ---------------------------------------------------------------------------
const activeTab = computed(() =>
  TABS.some((tab) => tab.key === route.query.tab) ? route.query.tab : "general",
);
const focusFloor = computed(() => {
  const n = Number(route.query.planta);
  return route.query.planta !== undefined && Number.isInteger(n) ? n : null;
});

function setTab(key) {
  router.push({ query: key === "general" ? {} : { tab: key } });
}

// Arrow keys move between tabs (WAI-ARIA tabs pattern)
const tabButtons = ref([]);
async function focusTab(index) {
  const next = TABS[(index + TABS.length) % TABS.length];
  setTab(next.key);
  await nextTick();
  tabButtons.value[TABS.indexOf(next)]?.focus();
}

function openFloor(floor) {
  const query = { tab: "plantas" };
  if (Number.isInteger(floor)) query.planta = String(floor);
  router.push({ query });
}

// ---------------------------------------------------------------------------
// Building and sensors (stores shared with "Mis edificios")
// ---------------------------------------------------------------------------
const siteId = computed(() => route.params.id);
const site = computed(() => sitesStore.siteById(siteId.value) ?? null);

const siteLoading = computed(
  () =>
    ["idle", "loading"].includes(sitesStore.status) && !sitesStore.sites.length,
);
const sitesError = computed(() =>
  sitesStore.status === "error"
    ? apiErrorMessage(sitesStore.error, "No se ha podido cargar el edificio.")
    : "",
);

const siteSensors = computed(() =>
  sensorsStore.sensors.filter((sensor) => sensor.site_id === siteId.value),
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
    // Without sensors the drawing says "sin sensor"
  }
}

function plural(n, one, many) {
  return `${n} ${n === 1 ? one : many}`;
}

// "Carrer de Verdi 40 · 3 plantas · 1 sótano · 2 sensores"
const siteSummary = computed(() => {
  const s = site.value;
  const parts = [];
  if (s.address) parts.push(s.address);
  parts.push(plural(s.floors, "planta", "plantas"));
  if (s.basements > 0) parts.push(plural(s.basements, "sótano", "sótanos"));
  parts.push(plural(siteSensors.value.length, "sensor", "sensores"));
  return parts.join(" · ");
});

// ---------------------------------------------------------------------------
// Alerts of this building, one list per state
// ---------------------------------------------------------------------------
const lists = reactive({ ACTIVE: [], ACKNOWLEDGED: [], RESOLVED: [] });
const alertsLoaded = ref(false);
const alertsError = ref("");

// Ignores answers that arrive after moving to another building
let requestId = 0;

async function loadAlerts({ silent = false } = {}) {
  const id = ++requestId;
  const site_id = siteId.value;
  if (!silent) alertsError.value = "";
  try {
    const states = Object.keys(lists);
    const pages = await Promise.all(
      states.map((state) => alertsService.getAlerts({ site_id, state })),
    );
    if (id !== requestId) return;
    states.forEach((state, i) => {
      // Filtered again: the mock adapter ignores `state` and `site_id`
      lists[state] = (pages[i].data.items ?? []).filter(
        (alert) => alert.state === state && alert.site_id === site_id,
      );
    });
    alertsLoaded.value = true;
    alertsError.value = "";
  } catch (err) {
    if (id !== requestId || silent) return;
    alertsError.value = apiErrorMessage(
      err,
      "No se han podido cargar los avisos.",
    );
  }
}

const SEVERITY_ORDER = { CRITICAL: 0, WARNING: 1 };

function time(value) {
  const ms = new Date(value).getTime();
  return Number.isNaN(ms) ? 0 : ms;
}

// Pending first, then urgent, then newest
const openAlerts = computed(() =>
  [...lists.ACTIVE, ...lists.ACKNOWLEDGED].sort(
    (a, b) =>
      (a.state === "ACTIVE" ? 0 : 1) - (b.state === "ACTIVE" ? 0 : 1) ||
      (SEVERITY_ORDER[a.severity] ?? 2) - (SEVERITY_ORDER[b.severity] ?? 2) ||
      time(b.created_at) - time(a.created_at),
  ),
);
const spotlight = computed(() => openAlerts.value[0] ?? null);

const allAlerts = computed(() => [
  ...lists.ACTIVE,
  ...lists.ACKNOWLEDGED,
  ...lists.RESOLVED,
]);

// Per floor: pending and en curso
const floorStates = computed(() => {
  const states = {};
  const add = (alert, key) => {
    if (!Number.isInteger(alert.floor)) return;
    states[alert.floor] ??= { pending: 0, inProgress: 0 };
    states[alert.floor][key] += 1;
  };
  lists.ACTIVE.forEach((alert) => add(alert, "pending"));
  lists.ACKNOWLEDGED.forEach((alert) => add(alert, "inProgress"));
  return states;
});

// ---------------------------------------------------------------------------
// Indicators
// ---------------------------------------------------------------------------
const indicators = computed(() => {
  const loaded = alertsLoaded.value;
  const pending = lists.ACTIVE.length;
  const connected = siteSensors.value.filter(
    (sensor) => pressureState(sensor).key !== "offline",
  ).length;
  return [
    {
      label: "Sin atender",
      value: loaded ? pending : "—",
      to: { query: { tab: "alertas" } },
      labelClass: "text-danger-dark",
      valueClass: pending > 0 ? "text-danger-dark" : "text-slate-900",
    },
    {
      label: "En curso",
      value: loaded ? lists.ACKNOWLEDGED.length : "—",
      to: { query: { tab: "alertas", estado: "en-curso" } },
      labelClass: "text-info-dark",
      valueClass: "text-slate-900",
    },
    {
      label: "Sensores conectados",
      value: `${connected} de ${siteSensors.value.length}`,
      to: { query: { tab: "plantas" } },
      labelClass: "text-slate-700",
      valueClass: "text-slate-900",
    },
  ];
});

// ---------------------------------------------------------------------------
// "Me encargo": the alert moves from Sin atender to En curso without reloading
// ---------------------------------------------------------------------------
const busyAlertId = ref(null);
const actionError = ref("");
const liveMessage = ref("");

async function acknowledge(id) {
  busyAlertId.value = id;
  actionError.value = "";
  try {
    const response = await alertsService.acknowledgeAlert(id);
    lists.ACTIVE = lists.ACTIVE.filter((alert) => alert.id !== id);
    if (response.data?.state === "ACKNOWLEDGED")
      lists.ACKNOWLEDGED = [response.data, ...lists.ACKNOWLEDGED];
    liveMessage.value = "Hecho: el aviso pasa a «En curso».";
    overviewStore.fetchOverview().catch(() => {});
  } catch (err) {
    actionError.value = apiErrorMessage(
      err,
      "No se ha podido guardar. Inténtalo de nuevo.",
    );
  } finally {
    busyAlertId.value = null;
  }
}

// ---------------------------------------------------------------------------
// Loading and refresh
// ---------------------------------------------------------------------------
// Another building: start again
watch(siteId, () => {
  alertsLoaded.value = false;
  actionError.value = "";
  loadAlerts();
});

// Coming back from the Alertas tab: "Me encargo" may have changed the lists
watch(activeTab, (tab) => {
  if (tab === "general") loadAlerts({ silent: true });
});

useAutoRefresh(
  () => Promise.all([loadSites(), loadSensors(), loadAlerts({ silent: true })]),
  REFRESH_MS,
);

onMounted(() => {
  // The stores may already have the data from "Mis edificios"
  if (!sitesStore.sites.length) loadSites();
  if (!sensorsStore.sensors.length) loadSensors();
  loadAlerts();
});
</script>
