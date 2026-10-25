<!--
  BUILDING FLOORS PANEL ("Plantas y sensores" tab of the building page)
  Moved as it was from the old open building of BuildingsView (F8) in F25;
  F26 redesigns it:
    - The building floor by floor (BuildingStack, F4) and the selected
      sensor with its 7-day pressure chart (SensorDetailPanel, F5, B7).
    - Alerts of the week by sensor and day (WeekAlertsGrid, B9).
  It opens on the most worrying sensor, or on the first sensor of
  `focusFloor` when the parent asks for a floor (click on the drawn
  building of "Vista general").
  Usage:
    <BuildingFloorsPanel :site="site" :sensors="sensors" :alerts="alerts"
                         :focus-floor="2" />
-->

<template>
  <div class="space-y-6">
    <EmptyState
      v-if="!sensors.length"
      icon="droplet"
      title="Este edificio todavía no tiene sensores"
      message="Cuando AquaGuard instale sensores, aparecerán aquí."
    />

    <div
      v-else
      class="grid grid-cols-1 items-start gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]"
    >
      <BuildingStack
        :name="site.name"
        :floors="site.floors"
        :basements="site.basements"
        :sensors="sensors"
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
          v-else
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
      <h2 id="week-alerts-title" class="mb-3 text-lg font-bold text-slate-900">
        Alertas de la semana por sensor
      </h2>
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
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";

import BuildingStack from "./BuildingStack.vue";
import SensorDetailPanel from "./SensorDetailPanel.vue";
import WeekAlertsGrid from "./WeekAlertsGrid.vue";
import LoadingState from "./LoadingState.vue";
import ErrorState from "./ErrorState.vue";
import EmptyState from "./EmptyState.vue";

import readingService from "../services/reading.service.js";
import analyticsService from "../services/analytics.service.js";
import { useAutoRefresh } from "../composables/useAutoRefresh";

const REFRESH_MS = 60 * 1000;
const DAY_MS = 24 * 60 * 60 * 1000;

const props = defineProps({
  // SiteResponse
  site: { type: Object, required: true },
  // SensorResponse list of this building
  sensors: { type: Array, default: () => [] },
  // Alerts of this building already loaded by the page (any state)
  alerts: { type: Array, default: () => [] },
  // Floor to open first (null: the most worrying sensor)
  focusFloor: { type: Number, default: null },
});

// ---------------------------------------------------------------------------
// Selected sensor and its 7-day series (B7)
// ---------------------------------------------------------------------------
const selectedId = ref(null);
const sidePanel = ref(null);
const selectedSensor = computed(
  () => props.sensors.find((sensor) => sensor.id === selectedId.value) ?? null,
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

// The first sensor of the asked floor, or the most worrying one
const HEALTH_ORDER = { CRITICAL: 0, WARNING: 1, OFFLINE: 2, OK: 3 };
function defaultSensorId() {
  const sorted = [...props.sensors].sort(
    (a, b) => (HEALTH_ORDER[a.health] ?? 4) - (HEALTH_ORDER[b.health] ?? 4),
  );
  if (props.focusFloor !== null) {
    const onFloor = sorted.find((sensor) => sensor.floor === props.focusFloor);
    if (onFloor) return onFloor.id;
  }
  return sorted[0]?.id ?? null;
}

watch(
  () => [props.sensors.length, props.focusFloor],
  () => {
    if (!selectedSensor.value || props.focusFloor !== null)
      selectedId.value = defaultSensorId();
  },
  { immediate: true },
);

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
  } catch {
    if (selectedId.value !== sensorId || silent) return;
    readingsError.value = "No se han podido cargar las lecturas.";
  } finally {
    if (selectedId.value === sensorId) readingsLoading.value = false;
  }
}

watch(selectedId, () => loadReadings());

// Alerts of the selected sensor in the last 7 days
const alertCount = computed(() => {
  if (!selectedId.value) return null;
  const since = Date.now() - 7 * DAY_MS;
  return props.alerts.filter(
    (alert) =>
      alert.sensor_id === selectedId.value &&
      new Date(alert.created_at).getTime() >= since,
  ).length;
});

// ---------------------------------------------------------------------------
// Alerts of the week by sensor and day (B9)
// ---------------------------------------------------------------------------
const weekly = ref(null);
const weeklyLoading = ref(false);
const weeklyError = ref("");

async function loadWeekly({ silent = false } = {}) {
  const id = props.site.id;
  if (!silent) {
    weeklyLoading.value = true;
    weeklyError.value = "";
  }
  try {
    const response = await analyticsService.getWeeklyAlerts({ site_id: id });
    if (props.site.id !== id) return;
    weekly.value = response.data;
    weeklyError.value = "";
  } catch {
    if (props.site.id !== id || silent) return;
    weeklyError.value = "No se han podido cargar las alertas de la semana.";
  } finally {
    weeklyLoading.value = false;
  }
}

useAutoRefresh(
  () =>
    Promise.all([loadWeekly({ silent: true }), loadReadings({ silent: true })]),
  REFRESH_MS,
);

onMounted(() => loadWeekly());
</script>
