<!--
  CLIENT ALERTS VIEW (F9-C)
  The client's week, day by day, for one building:
    - Building selector (only with more than one building) and week
      navigation. Both live in the URL (/app/alerts?site=<id>&week=YYYY-MM-DD,
      the Monday), so reloading and the back button keep them.
    - WeekAlertsGrid (F8) with GET /api/analytics/alerts/weekly (B9): alerts
      per sensor and day. Clicking a sensor filters the list; clicking it
      again removes the filter.
    - The alerts of that week (GET /api/alerts with site_id, created_from and
      created_to, B5) grouped by day, one AlertRow (F3) each.
  Acknowledge and resolve use stores/alerts.js, which replaces the row with
  the PATCH answer (state ACKNOWLEDGED or RESOLVED): the list is not reloaded.
  After resolving, the overview is asked again so the sidebar counter drops
  at once instead of on the next 30-second refresh.
  Days are UTC, the same as B9 groups them.
-->

<template>
  <div class="mx-auto max-w-7xl space-y-6">
    <header class="flex flex-wrap items-end justify-between gap-3">
      <div class="min-w-0">
        <h1 class="text-2xl font-bold text-slate-900">Alertas</h1>
        <p class="mt-1 text-sm text-slate-600">
          Tu semana día a día: reconoce las alertas que ya estás atendiendo y
          resuélvelas al terminar.
        </p>
      </div>

      <label
        v-if="sites.length > 1"
        class="flex flex-col gap-1 text-sm font-medium text-slate-700"
      >
        Edificio
        <select
          :value="siteId"
          class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800"
          @change="setQuery({ site: $event.target.value })"
        >
          <option v-for="item in sortedSites" :key="item.id" :value="item.id">
            {{ item.name }}
          </option>
        </select>
      </label>
    </header>

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
      message="Cuando AquaGuard dé de alta tu edificio, verás aquí sus alertas."
    />

    <template v-else>
      <!-- Week navigation -->
      <nav aria-label="Semana" class="flex flex-wrap items-center gap-2">
        <!-- Arrows and dates never wrap apart; on phones "Esta semana ·" is
             only read by screen readers, so the row fits in 375 px -->
        <div class="flex min-w-0 items-center gap-2">
          <button type="button" :class="navButton" @click="moveWeek(-1)">
            ‹ <span class="sr-only sm:not-sr-only">Semana anterior</span>
          </button>
          <p
            class="min-w-0 px-1 text-center text-sm font-semibold text-slate-800"
            aria-live="polite"
          >
            <span v-if="isCurrentWeek" class="sr-only sm:not-sr-only"
              >Esta semana · </span
            >{{ weekRange }}
          </p>
          <button
            type="button"
            :class="navButton"
            :disabled="isCurrentWeek"
            @click="moveWeek(1)"
          >
            <span class="sr-only sm:not-sr-only">Semana siguiente</span> ›
          </button>
        </div>
        <button
          v-if="!isCurrentWeek"
          type="button"
          :class="navButton"
          @click="setQuery({ week: null })"
        >
          Esta semana
        </button>
      </nav>

      <!-- Alerts per sensor and day (B9) -->
      <section
        class="rounded-xl border border-slate-200 bg-white p-5"
        aria-labelledby="week-grid-title"
      >
        <h2 id="week-grid-title" class="text-lg font-bold text-slate-900">
          Alertas por sensor y día
        </h2>
        <p class="mb-3 text-sm text-slate-600">
          Pulsa un sensor para ver solo sus alertas.
        </p>

        <LoadingState
          v-if="weeklyLoading"
          message="Cargando la semana…"
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
          :selected-id="sensorId"
          :site-name="site?.name ?? ''"
          @select="toggleSensor"
        />
      </section>

      <!-- Alerts of the week, day by day (B5) -->
      <section class="space-y-3" aria-labelledby="week-list-title">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <h2 id="week-list-title" class="text-lg font-bold text-slate-900">
            Alertas de la semana
          </h2>
          <p
            v-if="listReady && weekAlerts.length"
            class="text-sm text-slate-600"
          >
            {{ summaryText }}
          </p>
        </div>

        <div v-if="sensorId" class="flex flex-wrap items-center gap-2 text-sm">
          <span
            class="rounded-full bg-aqua-100 px-3 py-1 font-medium text-aqua-900"
          >
            Sensor: {{ sensorName }}
          </span>
          <button
            type="button"
            class="font-medium text-aqua-700 underline hover:text-aqua-900"
            @click="sensorId = null"
          >
            Ver todos los sensores
          </button>
        </div>

        <div
          v-if="actionError"
          class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
          role="alert"
        >
          {{ actionError }}
        </div>

        <ErrorState
          v-if="listError"
          title="No se han podido cargar las alertas"
          :message="listError"
          @retry="loadAlerts"
        />
        <LoadingState v-else-if="!listReady" message="Cargando alertas…" />
        <EmptyState
          v-else-if="!weekAlerts.length"
          icon="alert"
          :title="
            sensorId
              ? 'Este sensor no tuvo alertas esta semana'
              : 'Sin alertas esta semana'
          "
          :message="
            isCurrentWeek
              ? 'Si un sensor sale de su rango, la alerta aparecerá aquí.'
              : ''
          "
        />

        <div
          v-else
          class="overflow-x-auto rounded-xl border border-slate-200 bg-white"
        >
          <table class="min-w-full text-sm">
            <caption class="sr-only">
              Alertas de
              {{
                weekLabel
              }}
              por día
            </caption>
            <thead
              class="bg-slate-50 text-left text-xs uppercase text-slate-500"
            >
              <tr>
                <th scope="col" class="px-4 py-3">Alerta</th>
                <th scope="col" class="px-4 py-3">Sensor</th>
                <th scope="col" class="px-4 py-3">Severidad</th>
                <th scope="col" class="px-4 py-3">Estado</th>
                <th scope="col" class="px-4 py-3">Fecha</th>
                <th scope="col" class="px-4 py-3">Acciones</th>
              </tr>
            </thead>
            <tbody
              v-for="group in dayGroups"
              :key="group.day"
              class="divide-y divide-slate-100 border-t border-slate-200"
            >
              <tr class="bg-slate-50">
                <th
                  scope="rowgroup"
                  :colspan="COLUMNS"
                  class="px-4 py-2 text-left text-sm font-semibold text-slate-800"
                >
                  {{ group.label }}
                  <span class="font-normal text-slate-500"
                    >· {{ countText(group.alerts.length) }}</span
                  >
                </th>
              </tr>
              <tr v-if="!group.alerts.length">
                <td :colspan="COLUMNS" class="px-4 py-3 text-sm text-slate-500">
                  Sin alertas
                </td>
              </tr>
              <AlertRow
                v-for="alert in group.alerts"
                :key="alert.id"
                :alert="alert"
                :busy="busyAlertId === alert.id"
                :show-organization="false"
                @acknowledge="acknowledge"
                @resolve="resolve"
              />
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import AlertRow from "../../components/AlertRow.vue";
import WeekAlertsGrid from "../../components/WeekAlertsGrid.vue";
import LoadingState from "../../components/LoadingState.vue";
import ErrorState from "../../components/ErrorState.vue";
import EmptyState from "../../components/EmptyState.vue";

import { useSitesStore } from "../../stores/sites.js";
import { useAlertsStore } from "../../stores/alerts.js";
import { useOverviewStore } from "../../stores/overview.js";
import analyticsService from "../../services/analytics.service.js";
import { useAutoRefresh } from "../../composables/useAutoRefresh";

const REFRESH_MS = 60 * 1000;
// Columns of the table without the client one (AlertRow :show-organization="false")
const COLUMNS = 6;

const route = useRoute();
const router = useRouter();
const sitesStore = useSitesStore();
const alertsStore = useAlertsStore();
const overviewStore = useOverviewStore();

const navButton =
  "rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50";

// ---------------------------------------------------------------------------
// Days. Everything is UTC 'YYYY-MM-DD', the same as B9.
// ---------------------------------------------------------------------------
function isoDay(date) {
  return date.toISOString().slice(0, 10);
}

function addDays(day, n) {
  const date = new Date(`${day}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + n);
  return isoDay(date);
}

function mondayOf(day) {
  const weekday = new Date(`${day}T00:00:00Z`).getUTCDay();
  return addDays(day, -((weekday + 6) % 7));
}

// Updated on every refresh, so a page left open moves on to the new day
const today = ref(isoDay(new Date()));
const currentMonday = computed(() => mondayOf(today.value));

const weekStart = computed(() => {
  const fromUrl = route.query.week;
  if (typeof fromUrl !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(fromUrl))
    return currentMonday.value;
  if (Number.isNaN(new Date(`${fromUrl}T00:00:00Z`).getTime()))
    return currentMonday.value;
  const monday = mondayOf(fromUrl);
  // No future weeks: there is nothing to show yet
  return monday > currentMonday.value ? currentMonday.value : monday;
});

const isCurrentWeek = computed(() => weekStart.value === currentMonday.value);
const weekDays = computed(() =>
  Array.from({ length: 7 }, (_, i) => addDays(weekStart.value, i)),
);

const shortDate = new Intl.DateTimeFormat("es-ES", {
  day: "numeric",
  month: "short",
  timeZone: "UTC",
});
const shortDateYear = new Intl.DateTimeFormat("es-ES", {
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});
const longDay = new Intl.DateTimeFormat("es-ES", {
  weekday: "long",
  day: "numeric",
  month: "long",
  timeZone: "UTC",
});

// "12 oct – 18 oct 2026"; weekLabel adds "Esta semana · " for the current one
const weekRange = computed(() => {
  const start = new Date(`${weekStart.value}T00:00:00Z`);
  const end = new Date(`${addDays(weekStart.value, 6)}T00:00:00Z`);
  return `${shortDate.format(start).replace(".", "")} – ${shortDateYear.format(end).replace(".", "")}`;
});
const weekLabel = computed(() =>
  isCurrentWeek.value ? `Esta semana · ${weekRange.value}` : weekRange.value,
);

// "Hoy, lunes 12 de octubre"
function dayLabel(day) {
  const text = longDay.format(new Date(`${day}T00:00:00Z`));
  const name = text.charAt(0).toUpperCase() + text.slice(1);
  if (day === today.value) return `Hoy, ${text}`;
  if (day === addDays(today.value, -1)) return `Ayer, ${text}`;
  return name;
}

function countText(n) {
  return `${n} ${n === 1 ? "alerta" : "alertas"}`;
}

// ---------------------------------------------------------------------------
// URL: ?site=<id>&week=<Monday>. null removes the parameter.
// ---------------------------------------------------------------------------
function setQuery(patch) {
  const query = { ...route.query };
  for (const [key, value] of Object.entries(patch)) {
    if (value) query[key] = value;
    else delete query[key];
  }
  router.push({ query });
}

function moveWeek(n) {
  const monday = addDays(weekStart.value, 7 * n);
  setQuery({ week: monday >= currentMonday.value ? null : monday });
}

// ---------------------------------------------------------------------------
// Buildings: the one in the URL, or the most worrying one
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

const STATUS_ORDER = { CRITICAL: 0, WARNING: 1, OK: 2 };
const sortedSites = computed(() =>
  [...sites.value].sort(
    (a, b) =>
      (STATUS_ORDER[a.status] ?? 3) - (STATUS_ORDER[b.status] ?? 3) ||
      a.name.localeCompare(b.name, "es"),
  ),
);

const siteId = computed(() => {
  const fromUrl = route.query.site;
  if (fromUrl && sitesStore.siteById(fromUrl)) return fromUrl;
  return sortedSites.value[0]?.id ?? null;
});

const site = computed(() =>
  siteId.value ? sitesStore.siteById(siteId.value) : null,
);

async function loadSites() {
  try {
    await sitesStore.fetchSites();
  } catch {
    // The store exposes the error state to the view
  }
}

// ---------------------------------------------------------------------------
// Alerts per sensor and day (B9)
// ---------------------------------------------------------------------------
const weekly = ref(null);
const weeklyLoading = ref(false);
const weeklyError = ref("");

const weekKey = computed(() => `${siteId.value}|${weekStart.value}`);

// silent: refresh without the spinner, keeping the grid if it fails
async function loadWeekly({ silent = false } = {}) {
  const key = weekKey.value;
  if (!siteId.value) return;
  if (!silent) {
    weeklyLoading.value = true;
    weeklyError.value = "";
    weekly.value = null;
  }
  try {
    const response = await analyticsService.getWeeklyAlerts({
      site_id: siteId.value,
      week_start: weekStart.value,
    });
    if (weekKey.value !== key) return;
    weekly.value = response.data;
    weeklyError.value = "";
  } catch (err) {
    if (weekKey.value !== key || silent) return;
    weeklyError.value =
      err?.message || "No se han podido cargar las alertas de la semana.";
  } finally {
    if (weekKey.value === key) weeklyLoading.value = false;
  }
}

// ---------------------------------------------------------------------------
// Alerts of the week (B5). The store keeps the list; the view remembers which
// week it belongs to, so it never shows the alerts of the previous one.
// ---------------------------------------------------------------------------
const alertParams = computed(() => ({
  site_id: siteId.value,
  created_from: `${weekStart.value}T00:00:00Z`,
  created_to: `${addDays(weekStart.value, 7)}T00:00:00Z`,
}));
const alertsKey = computed(() => JSON.stringify(alertParams.value));
const loadedKey = ref(null);

const listReady = computed(
  () => loadedKey.value === alertsKey.value && alertsStore.status !== "error",
);
const listError = computed(() =>
  alertsStore.status === "error"
    ? alertsStore.error?.message || "Inténtalo de nuevo en unos segundos."
    : "",
);

async function loadAlerts() {
  if (!siteId.value) return;
  const key = alertsKey.value;
  try {
    await alertsStore.fetchAlerts(alertParams.value);
    if (alertsKey.value === key) loadedKey.value = key;
  } catch {
    // The store exposes the error state to the view
  }
}

const sensorId = ref(null);

function toggleSensor(id) {
  sensorId.value = sensorId.value === id ? null : id;
}

const sensorName = computed(() => {
  const row = weekly.value?.rows?.find(
    (item) => item.sensor_id === sensorId.value,
  );
  if (row) return row.sensor_name;
  return (
    alertsStore.alerts.find((alert) => alert.sensor_id === sensorId.value)
      ?.sensor_name ?? "sensor"
  );
});

function alertDay(alert) {
  const date = new Date(alert.created_at);
  return Number.isNaN(date.getTime()) ? null : isoDay(date);
}

const weekAlerts = computed(() => {
  if (!listReady.value) return [];
  const days = new Set(weekDays.value);
  return alertsStore.alerts.filter(
    (alert) =>
      alert.site_id === siteId.value &&
      days.has(alertDay(alert)) &&
      (!sensorId.value || alert.sensor_id === sensorId.value),
  );
});

// One group per day up to today, Monday first; newest alert first in each day
const dayGroups = computed(() =>
  weekDays.value
    .filter((day) => day <= today.value)
    .map((day) => ({
      day,
      label: dayLabel(day),
      alerts: weekAlerts.value
        .filter((alert) => alertDay(alert) === day)
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at)),
    })),
);

// "5 alertas · 2 sin reconocer · 1 reconocida · 2 resueltas"
const summaryText = computed(() => {
  const count = (state) =>
    weekAlerts.value.filter((alert) => alert.state === state).length;
  const active = count("ACTIVE");
  const acknowledged = count("ACKNOWLEDGED");
  const resolved = count("RESOLVED");
  return [
    countText(weekAlerts.value.length),
    `${active} sin reconocer`,
    `${acknowledged} ${acknowledged === 1 ? "reconocida" : "reconocidas"}`,
    `${resolved} ${resolved === 1 ? "resuelta" : "resueltas"}`,
  ].join(" · ");
});

// ---------------------------------------------------------------------------
// Acknowledge / resolve: the store replaces the row with the PATCH answer
// ---------------------------------------------------------------------------
const busyAlertId = ref(null);
const actionError = ref("");

async function runAction(id, action, fallback) {
  busyAlertId.value = id;
  actionError.value = "";
  try {
    await action(id);
    return true;
  } catch (err) {
    actionError.value = err?.message || fallback;
    return false;
  } finally {
    busyAlertId.value = null;
  }
}

function acknowledge(id) {
  return runAction(
    id,
    alertsStore.acknowledgeAlert,
    "No se ha podido reconocer la alerta.",
  );
}

async function resolve(id) {
  if (
    await runAction(
      id,
      alertsStore.resolveAlert,
      "No se ha podido resolver la alerta.",
    )
  ) {
    // open_alerts of the sidebar counter comes from the overview (B9)
    overviewStore.fetchOverview().catch(() => {});
  }
}

// ---------------------------------------------------------------------------
// Loading and refresh
// ---------------------------------------------------------------------------
// Another building: the sensor filter belonged to the previous one
watch(siteId, () => {
  sensorId.value = null;
});

// Another building or week (and the first one, once the buildings are known)
watch(
  weekKey,
  () => {
    actionError.value = "";
    loadWeekly();
    loadAlerts();
  },
  { immediate: true },
);

function refresh() {
  today.value = isoDay(new Date());
  loadWeekly({ silent: true });
  loadAlerts();
}

useAutoRefresh(refresh, REFRESH_MS);

onMounted(loadSites);
</script>
