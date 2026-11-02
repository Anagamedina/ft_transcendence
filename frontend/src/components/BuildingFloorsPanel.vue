<!--
  BUILDING FLOORS PANEL ("Plantas y sensores" tab of the building page)
  Moved from the old open building of BuildingsView (F8) in F25 and
  redesigned in F26:
    - The building drawn as in "Vista general" (BuildingDrawing with
      show-sensors), so both tabs show the same building, and the selected
      sensor (SensorDetailPanel): gauge, pressure in words, range, last
      reading and the chart with 24 h · 7 días · 30 días (B7). The periods
      are the admin ones (PERIODS in stores/adminSensors.js), so both areas
      show the same chart.
    - "Ver alertas de este sensor" opens the Alertas tab filtered by sensor
      (?sensor=, read by ClientAlertsPanel).
    - The week by sensor lives only in "Vista general" (WeekStateGrid), so
      this tab does not repeat it.
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
      class="grid grid-cols-1 items-start gap-6 lg:grid-cols-[minmax(0,360px)_minmax(0,1fr)]"
    >
      <section
        class="rounded-xl border border-slate-200 bg-white p-5"
        :aria-label="`${site.name}: edificio planta a planta`"
      >
        <BuildingDrawing
          :name="site.name"
          :floors="site.floors"
          :basements="site.basements"
          :states="floorStates"
          :sensors="sensors"
          show-sensors
          :selected-id="selectedId"
          @select-sensor="selectSensor"
        />
      </section>

      <div ref="sidePanel">
        <SensorDetailPanel
          v-if="selectedSensor"
          :sensor="selectedSensor"
          :readings="readings"
          :alert-count="alertCount"
          :periods="PERIODS"
          :period="period"
          @update:period="period = $event"
          :alerts-to="{ query: { tab: 'alertas', sensor: selectedSensor.id } }"
          :loading="readingsLoading"
          :error="readingsError"
          @retry="loadReadings()"
        />
        <EmptyState
          v-else
          icon="droplet"
          title="Elige un sensor"
          message="Toca un sensor del edificio para ver su presión y su gráfica."
          compact
        />
      </div>
    </div>

  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from "vue";

import BuildingDrawing from "./BuildingDrawing.vue";
import SensorDetailPanel from "./SensorDetailPanel.vue";
import EmptyState from "./EmptyState.vue";

import readingService from "../services/reading.service.js";
import { PERIODS } from "../stores/adminSensors.js";
import { REFRESH_MS, useAutoRefresh } from "../composables/useAutoRefresh";

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
// Selected sensor and its series for the chosen period (B7)
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

// Chart period: same default as before (7 days)
const period = ref("7d");

const readings = ref([]);
const readingsLoading = ref(false);
const readingsError = ref("");

// silent: refresh without the spinner, keeping the chart if it fails
async function loadReadings({ silent = false } = {}) {
  const sensorId = selectedId.value;
  const periodKey = period.value;
  if (!sensorId) return;
  if (!silent) {
    readingsLoading.value = true;
    readingsError.value = "";
    readings.value = [];
  }
  try {
    const { days, bucket } = PERIODS[period.value];
    const response = await readingService.getSensorSeries(sensorId, {
      days,
      bucket,
    });
    // An answer for another sensor or period arrived late: ignore it
    if (selectedId.value !== sensorId || period.value !== periodKey) return;
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

// A new sensor or a new period: load again, without reloading the page
watch([selectedId, period], () => loadReadings());

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

// Per floor: pending and en curso alerts (same as "Vista general")
const floorStates = computed(() => {
  const states = {};
  for (const alert of props.alerts) {
    if (!Number.isInteger(alert.floor)) continue;
    const key =
      alert.state === "ACTIVE"
        ? "pending"
        : alert.state === "ACKNOWLEDGED"
          ? "inProgress"
          : null;
    if (!key) continue;
    states[alert.floor] ??= { pending: 0, inProgress: 0 };
    states[alert.floor][key] += 1;
  }
  return states;
});

useAutoRefresh(() => loadReadings({ silent: true }), REFRESH_MS);
</script>
