<!--
  CLIENT ALERTS PANEL (F21, panel since F25)
  The client's alerts, used in two places:
    - /app/alerts (AlertsView): every building, with a building filter when
      there is more than one.
    - The "Alertas" tab of the building page (F25): :fixed-site-id, so only
      that building and no filter.
  Content:
    - Three tabs by state (field `state` of GET /api/alerts):
        Sin atender (ACTIVE) · En curso (ACKNOWLEDGED) · Arregladas (RESOLVED),
      each with its count (`total` of the page).
    - Open tabs: a grid of AlertCard, urgent first, then newest.
    - "Arregladas": ResolvedAlertsTable, most recently fixed first, 10 at a
      time ("Ver 10 más"), count on top, period and type filters.
    - "Me encargo" (PATCH /api/alerts/{id}/acknowledge): the card moves to
      "En curso" at once, without reloading the page.
    - Severity legend (Crítica / Leve, from useLabels), fixed on every tab.
  All words come from useLabels: the same for client, admin and landing.
  "Ver alertas de este sensor" (F26) adds ?sensor=<id>: only that sensor,
  with a removable chip and the tab counts of that sensor.
  The state tab lives in the URL under `stateKey` (?tab= on /app/alerts,
  ?estado= on the building page, whose own tabs use ?tab=); the building
  filter under ?site=.
  Only AquaGuard closes alerts: the client has no "resolve" button.
  Usage:
    <ClientAlertsPanel />
    <ClientAlertsPanel :fixed-site-id="site.id" state-key="estado" />
-->

<template>
  <div class="space-y-6">
    <div v-if="!fixedSiteId && sites.length > 1" class="flex justify-end">
      <label class="flex flex-col gap-1 text-sm font-medium text-slate-700">
        Edificio
        <select
          :value="siteId ?? ''"
          class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800"
          @change="setQuery({ site: $event.target.value || null })"
        >
          <option value="">Todos los edificios</option>
          <option v-for="item in sortedSites" :key="item.id" :value="item.id">
            {{ item.name }}
          </option>
        </select>
      </label>
    </div>

    <!-- Sensor filter from "Ver alertas de este sensor" (F26) -->
    <div v-if="sensorId" class="flex flex-wrap items-center gap-2 text-sm">
      <span class="text-slate-600">Solo el sensor</span>
      <span
        class="inline-flex items-center gap-1 rounded-full bg-aqua-100 py-1 pl-3 pr-1 font-semibold text-aqua-900"
      >
        {{ sensorName }}
        <button
          type="button"
          class="flex h-6 w-6 items-center justify-center rounded-full hover:bg-white focus:outline-none focus-visible:ring-2 focus-visible:ring-aqua-600"
          :aria-label="`Quitar el filtro del sensor ${sensorName}`"
          @click="setQuery({ sensor: null })"
        >
          <span aria-hidden="true">×</span>
        </button>
      </span>
    </div>

    <!-- Tabs by state -->
    <div
      role="tablist"
      aria-label="Estado de las alertas"
      class="grid grid-cols-3 border-b border-slate-200 sm:flex sm:gap-1"
    >
      <button
        v-for="(tab, index) in TABS"
        :id="`alerts-tab-${tab.slug}`"
        :key="tab.slug"
        ref="tabButtons"
        type="button"
        role="tab"
        :aria-selected="tab.slug === activeTab.slug"
        :aria-controls="`alerts-panel-${tab.slug}`"
        :tabindex="tab.slug === activeTab.slug ? 0 : -1"
        class="-mb-px flex min-w-0 items-center justify-center gap-1.5 border-b-2 px-1 py-2.5 text-xs font-semibold sm:justify-start sm:gap-2 sm:px-3 sm:text-sm"
        :class="
          tab.slug === activeTab.slug
            ? 'border-aqua-600 text-aqua-700'
            : 'border-transparent text-slate-600 hover:text-slate-900'
        "
        @click="selectTab(tab.slug)"
        @keydown.right.prevent="focusTab(index + 1)"
        @keydown.left.prevent="focusTab(index - 1)"
      >
        <span
          class="h-2 w-2 rounded-full"
          :class="toneClasses(tab.tone).dot"
          aria-hidden="true"
        ></span>
        {{ tab.text }}
        <span
          class="rounded-full bg-slate-100 px-1.5 py-0.5 text-xs font-semibold text-slate-800 sm:px-2"
        >
          {{ tabCount(tab.state) ?? "–" }}
        </span>
      </button>
    </div>

    <!-- Active tab -->
    <section
      :id="`alerts-panel-${activeTab.slug}`"
      role="tabpanel"
      :aria-labelledby="`alerts-tab-${activeTab.slug}`"
      class="space-y-3"
    >
      <!-- Severity legend: same pills as the cards, the same on every tab -->
      <ul
        class="flex flex-col gap-1.5 text-sm text-slate-700 sm:flex-row sm:flex-wrap sm:gap-x-6"
        aria-label="Qué significa cada gravedad"
      >
        <li
          v-for="item in LEGEND"
          :key="item.text"
          class="flex items-center gap-2"
        >
          <span
            class="inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold"
            :class="toneClasses(item.tone).pill"
          >
            <span class="h-3.5 w-3.5" aria-hidden="true"
              ><AppIcon name="alert"
            /></span>
            {{ item.text }}
          </span>
          {{ item.help }}
        </li>
      </ul>

      <!-- Filters of "Arregladas" -->
      <div
        v-if="activeTab.state === 'RESOLVED'"
        class="flex flex-wrap items-end gap-3"
      >
        <label class="flex flex-col gap-1 text-sm font-medium text-slate-700">
          Arregladas en
          <select
            v-model="period"
            class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800"
          >
            <option
              v-for="item in PERIODS"
              :key="item.value"
              :value="item.value"
            >
              {{ item.text }}
            </option>
          </select>
        </label>
        <label class="flex flex-col gap-1 text-sm font-medium text-slate-700">
          Tipo
          <select
            v-model="type"
            class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800"
          >
            <option value="">Todos</option>
            <option v-for="item in TYPES" :key="item" :value="item">
              {{ label("AlertType", item) }}
            </option>
          </select>
        </label>
        <button
          v-if="filtersOn"
          type="button"
          class="py-2 text-sm font-medium text-aqua-700 underline hover:text-aqua-900"
          @click="clearFilters"
        >
          Quitar filtros
        </button>
        <!-- Result count, on top so it is seen before the list -->
        <p
          v-if="loaded && !loadError"
          class="py-2 text-sm font-medium text-slate-700 sm:ml-auto"
          aria-live="polite"
        >
          {{ resultText }}
        </p>
      </div>

      <div
        v-if="actionError"
        class="rounded-lg border border-danger-light bg-danger-light p-3 text-sm text-danger-dark"
        role="alert"
      >
        {{ actionError }}
      </div>

      <ErrorState
        v-if="loadError"
        title="No se han podido cargar las alertas"
        :message="loadError"
        @retry="loadAll()"
      />
      <LoadingState v-else-if="!loaded" message="Cargando alertas…" />
      <EmptyState
        v-else-if="!visibleAlerts.length"
        :icon="activeTab.emptyIcon"
        :title="
          filtersOn
            ? 'Ningún aviso arreglado con estos filtros'
            : activeTab.emptyTitle
        "
        :message="
          filtersOn ? 'Prueba con otro periodo o tipo.' : activeTab.emptyMessage
        "
      />

      <template v-else>
        <ResolvedAlertsTable
          v-if="activeTab.state === 'RESOLVED'"
          :alerts="shownAlerts"
          caption="Avisos arreglados"
        />
        <ul v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <li v-for="alert in visibleAlerts" :key="alert.id">
            <AlertCard
              :alert="alert"
              :busy="busyAlertId === alert.id"
              @acknowledge="acknowledge"
            />
          </li>
        </ul>
        <div
          v-if="
            activeTab.state === 'RESOLVED' &&
            shownAlerts.length < visibleAlerts.length
          "
          class="flex justify-center"
        >
          <button
            type="button"
            class="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-aqua-700 hover:bg-slate-50"
            @click="limit += PAGE_STEP"
          >
            Ver
            {{ Math.min(PAGE_STEP, visibleAlerts.length - shownAlerts.length) }}
            más
          </button>
        </div>
      </template>
    </section>

    <!-- Announces the move to "En curso" to screen readers -->
    <p class="sr-only" aria-live="polite">{{ liveMessage }}</p>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import AppIcon from "./AppIcon.vue";
import AlertCard from "./AlertCard.vue";
import ResolvedAlertsTable from "./ResolvedAlertsTable.vue";
import LoadingState from "./LoadingState.vue";
import ErrorState from "./ErrorState.vue";
import EmptyState from "./EmptyState.vue";

import alertsService from "../services/alerts.service.js";
import { useSitesStore } from "../stores/sites.js";
import { useOverviewStore } from "../stores/overview.js";
import { useLabels } from "../composables/useLabels";
import { apiErrorMessage } from "../utils/apiError.js";
import { REFRESH_MS, useAutoRefresh } from "../composables/useAutoRefresh";

const props = defineProps({
  // Show only this building and hide the building filter
  fixedSiteId: { type: String, default: null },
  // URL query key for the state tab
  stateKey: { type: String, default: "tab" },
});

// Backend limit (page_size max 100)
const PAGE_SIZE = 100;

const { label, help, tone, toneClasses } = useLabels();

// Severity legend: same words and tones as AlertCard (useLabels)
const LEGEND = ["CRITICAL", "WARNING"].map((value) => ({
  text: label("AlertSeverity", value),
  tone: tone("AlertSeverity", value),
  help: help("AlertSeverity", value),
}));

// slug: value in the URL (unchanged, so old links still work); state: backend value

const TABS = [
  {
    slug: "pendiente",
    state: "ACTIVE",
    text: label("AlertState", "ACTIVE"),
    tone: "danger",
    emptyIcon: "droplet",
    emptyTitle: "No tienes nada sin atender",
    emptyMessage: "Si un sensor detecta un problema, el aviso aparecerá aquí.",
  },
  {
    slug: "en-curso",
    state: "ACKNOWLEDGED",
    text: label("AlertState", "ACKNOWLEDGED"),
    tone: "info",
    emptyIcon: "droplet",
    emptyTitle: "Nada en curso",
    emptyMessage: "Cuando pulses «Me encargo» en un aviso, lo verás aquí.",
  },
  {
    slug: "arreglado",
    state: "RESOLVED",
    text: "Arregladas",
    tone: "success",
    emptyIcon: "droplet",
    emptyTitle: "Todavía no hay avisos arreglados",
    emptyMessage: "",
  },
];

const route = useRoute();
const router = useRouter();
const sitesStore = useSitesStore();
const overviewStore = useOverviewStore();

// ---------------------------------------------------------------------------
// URL: ?<stateKey>=<slug>&site=<id>. null removes the parameter.
// ---------------------------------------------------------------------------
function setQuery(patch) {
  const query = { ...route.query };
  for (const [key, value] of Object.entries(patch)) {
    if (value) query[key] = value;
    else delete query[key];
  }
  router.push({ query });
}

const activeTab = computed(
  () => TABS.find((tab) => tab.slug === route.query[props.stateKey]) ?? TABS[0],
);

function selectTab(slug) {
  // The first tab is the default: keep the URL clean
  setQuery({ [props.stateKey]: slug === TABS[0].slug ? null : slug });
}

// Arrow keys move between tabs (WAI-ARIA tabs pattern)
const tabButtons = ref([]);
async function focusTab(index) {
  const next = TABS[(index + TABS.length) % TABS.length];
  selectTab(next.slug);
  await nextTick();
  tabButtons.value[TABS.indexOf(next)]?.focus();
}

// ---------------------------------------------------------------------------
// Buildings (only for the filter)
// ---------------------------------------------------------------------------
const sites = computed(() => sitesStore.sites);

const sortedSites = computed(() =>
  [...sites.value].sort((a, b) => a.name.localeCompare(b.name, "es")),
);

// The fixed building; else the one in the URL if it is one of the client's;
// otherwise all
const siteId = computed(() => {
  if (props.fixedSiteId) return props.fixedSiteId;
  const fromUrl = route.query.site;
  return fromUrl && sitesStore.siteById(fromUrl) ? fromUrl : null;
});

// ---------------------------------------------------------------------------
// Sensor filter (?sensor=<id>), applied in the front to the loaded lists
// ---------------------------------------------------------------------------
const sensorId = computed(() => route.query.sensor || null);

const sensorName = computed(() => {
  for (const list of Object.values(lists)) {
    const found = list.find((alert) => alert.sensor_id === sensorId.value);
    if (found?.sensor_name) return found.sensor_name;
  }
  return "elegido";
});

function ofSensor(alert) {
  return !sensorId.value || alert.sensor_id === sensorId.value;
}

// Server totals; with a sensor, the count of its loaded alerts
function tabCount(state) {
  if (!sensorId.value) return counts[state];
  return loaded.value ? lists[state].filter(ofSensor).length : null;
}

// ---------------------------------------------------------------------------
// Alerts: one request per state, so every tab has its real count
// ---------------------------------------------------------------------------
const lists = reactive({ ACTIVE: [], ACKNOWLEDGED: [], RESOLVED: [] });
const counts = reactive({ ACTIVE: null, ACKNOWLEDGED: null, RESOLVED: null });
const loaded = ref(false);
const loadError = ref("");

// Ignores answers that arrive after the building changed
let requestId = 0;

async function loadAll({ silent = false } = {}) {
  const id = ++requestId;
  if (!silent) {
    loaded.value = false;
    loadError.value = "";
  }
  const params = { page_size: PAGE_SIZE };
  if (siteId.value) params.site_id = siteId.value;

  try {
    const pages = await Promise.all(
      TABS.map((tab) =>
        alertsService.getAlerts({ ...params, state: tab.state }),
      ),
    );
    if (id !== requestId) return;
    TABS.forEach((tab, i) => {
      // Filtered again here too: the mock adapter ignores `state`
      const items = (pages[i].data.items ?? []).filter(
        (alert) =>
          alert.state === tab.state &&
          (!siteId.value || alert.site_id === siteId.value),
      );
      lists[tab.state] = items;
      counts[tab.state] = Math.max(pages[i].data.total ?? 0, items.length);
    });
    loaded.value = true;
    loadError.value = "";
  } catch (err) {
    if (id !== requestId || silent) return;
    loadError.value = apiErrorMessage(
      err,
      "Inténtalo de nuevo en unos segundos.",
    );
  }
}

// ---------------------------------------------------------------------------
// Filters of "Arregladas": period by fix date and alert type
// ---------------------------------------------------------------------------
const DAY_MS = 24 * 60 * 60 * 1000;
const PERIODS = [
  { value: "7", text: "Últimos 7 días" },
  { value: "30", text: "Últimos 30 días" },
  { value: "all", text: "Todo" },
];
const TYPES = ["HIGH_PRESSURE", "LOW_PRESSURE", "SENSOR_OFFLINE"];

const period = ref("all");
const type = ref("");
const filtersOn = computed(
  () =>
    activeTab.value.state === "RESOLVED" &&
    (period.value !== "all" || type.value !== ""),
);

function clearFilters() {
  period.value = "all";
  type.value = "";
}

function passesFilters(alert) {
  if (!filtersOn.value) return true;
  if (type.value && alert.type !== type.value) return false;
  if (period.value !== "all") {
    const since = Date.now() - Number(period.value) * DAY_MS;
    if (time(alert.resolved_at) < since) return false;
  }
  return true;
}

// "Arregladas" shows PAGE_STEP rows and grows with "Ver más"
const PAGE_STEP = 10;
const limit = ref(PAGE_STEP);
const shownAlerts = computed(() => visibleAlerts.value.slice(0, limit.value));

// Back to the first rows when the list changes
watch([activeTab, period, type, siteId, sensorId], () => {
  limit.value = PAGE_STEP;
});

// "10 de 21 avisos con estos filtros" / "23 avisos arreglados"
const resultText = computed(() => {
  const shown = shownAlerts.value.length;
  const total = visibleAlerts.value.length;
  const noun = total === 1 ? "aviso" : "avisos";
  const tail = filtersOn.value
    ? "con estos filtros"
    : total === 1
      ? "arreglado"
      : "arreglados";
  return shown < total
    ? `${shown} de ${total} ${noun} ${tail}`
    : `${total} ${noun} ${tail}`;
});

const SEVERITY_ORDER = { CRITICAL: 0, WARNING: 1 };

function time(value) {
  const ms = new Date(value).getTime();
  return Number.isNaN(ms) ? 0 : ms;
}

// Critical first, then newest. "Arregladas": most recently fixed first.
const visibleAlerts = computed(() => {
  const items = lists[activeTab.value.state]
    .filter(ofSensor)
    .filter(passesFilters);
  if (activeTab.value.state === "RESOLVED")
    return items.sort((a, b) => time(b.resolved_at) - time(a.resolved_at));
  return items.sort(
    (a, b) =>
      (SEVERITY_ORDER[a.severity] ?? 2) - (SEVERITY_ORDER[b.severity] ?? 2) ||
      time(b.created_at) - time(a.created_at),
  );
});

// ---------------------------------------------------------------------------
// "Me encargo": move the card from Sin atender to En curso without reloading
// ---------------------------------------------------------------------------
const busyAlertId = ref(null);
const actionError = ref("");
const liveMessage = ref("");

async function acknowledge(id) {
  busyAlertId.value = id;
  actionError.value = "";
  try {
    const response = await alertsService.acknowledgeAlert(id);
    const updated = response.data;
    lists.ACTIVE = lists.ACTIVE.filter((alert) => alert.id !== id);
    counts.ACTIVE = Math.max((counts.ACTIVE ?? 1) - 1, 0);
    if (updated?.state === "ACKNOWLEDGED") {
      lists.ACKNOWLEDGED = [updated, ...lists.ACKNOWLEDGED];
      counts.ACKNOWLEDGED = (counts.ACKNOWLEDGED ?? 0) + 1;
    }
    liveMessage.value = "Hecho: el aviso pasa a «En curso».";
    // Sidebar counter comes from the overview
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
watch(siteId, () => {
  actionError.value = "";
  loadAll();
});

watch(activeTab, () => {
  actionError.value = "";
});

useAutoRefresh(() => loadAll({ silent: true }), REFRESH_MS);

onMounted(() => {
  sitesStore.fetchSites().catch(() => {
    // The filter simply does not appear without buildings
  });
  loadAll();
});
</script>