<!--
  SENSOR SIDE PANEL (#283)
  Opens on the right when a sensor is clicked, like the alert panel:

    detail  what matters first ("Presión alta · 4,8 bar · el aparato
            funciona", or "Sin lecturas desde hace 9 h"), the pressure chart
            (24 h · 7 días · 30 días), the device data, its last alerts and
            "Ajustar umbrales"
    edit    SensorForm with its name, floor and thresholds
    create  SensorForm for a new sensor in the chosen building (and floor,
            from "+ Instalar aquí")

  The parent saves (it owns the stores); the panel only emits `save`.
  Esc closes; Tab stays inside the panel.
-->

<template>
  <Teleport to="body">
    <!-- z-[70]: above the mobile menu button of the Sidebar (z-[60]) -->
    <div v-if="open" class="fixed inset-0 z-[70] flex justify-end">
      <div class="absolute inset-0 bg-slate-900/30" aria-hidden="true" @click="close"></div>

      <aside
        ref="panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="sensor-panel-title"
        class="relative flex h-full w-full max-w-md flex-col overflow-y-auto bg-white shadow-xl"
        @keydown.esc.prevent="close"
        @keydown.tab="trapFocus"
      >
        <header class="flex flex-col gap-1.5 border-b border-slate-200 px-5 pb-4 pt-4">
          <div class="flex items-center gap-2">
            <span
              v-if="sensor && mode !== 'create'"
              class="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-bold"
              :class="offline ? 'bg-slate-200 text-slate-700' : 'bg-slate-100 text-slate-700'"
              :title="offline ? '' : 'El aparato envía lecturas: la presión se ve abajo'"
            >
              <span class="h-1.5 w-1.5 rounded-full" :class="offline ? 'bg-slate-500' : 'bg-success'"></span>
              {{ offline ? "Sin conexión" : "Envía lecturas" }}
            </span>
            <span v-if="sensor && mode !== 'create'" class="text-xs text-slate-500">{{ sensor.external_id }}</span>
            <button
              ref="closeButton"
              type="button"
              class="ml-auto flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100"
              aria-label="Cerrar"
              @click="close"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M6 6l12 12M18 6 6 18" />
              </svg>
            </button>
          </div>
          <h2 id="sensor-panel-title" class="text-xl font-bold text-slate-900">
            {{ mode === "create" ? "Nuevo sensor" : sensor?.name }}
          </h2>
          <p v-if="mode !== 'create' && sensor" class="text-sm text-slate-600">
            {{ sensor.organization_name }} · {{ sensor.site_name }} · {{ floorLabel(sensor.floor ?? 0) }}
          </p>
        </header>

        <!-- DETAIL -->
        <div v-if="mode === 'detail' && sensor" class="flex flex-1 flex-col gap-5 px-5 py-5 text-sm">
          <div class="rounded-xl p-4" :class="headline.box">
            <template v-if="offline">
              <p class="font-bold text-slate-900">
                {{ sensor.last_seen_at ? `Sin lecturas desde hace ${since(sensor.last_seen_at)}` : "Nunca ha enviado lecturas" }}
              </p>
              <p class="mt-1 text-slate-600">
                <template v-if="sensor.last_seen_at">
                  Última: {{ formatPressure(sensor.last_value, sensor.unit) }} a las {{ formatTime(sensor.last_seen_at) }}.
                </template>
                Revisa la alimentación y la red del sensor.
              </p>
            </template>
            <template v-else>
              <p class="text-[13px] font-bold" :class="headline.title">{{ headline.text }}</p>
              <p>
                <span class="text-3xl font-bold" :class="valueClass">{{ formatPressure(sensor.last_value, sensor.unit) }}</span>
                <span class="text-slate-500"> · {{ ago }}</span>
              </p>
              <p class="mt-1 text-slate-600">{{ headline.sub }}</p>
            </template>
          </div>

          <section aria-labelledby="sensor-chart-title" class="flex flex-col gap-2">
            <div class="flex items-center justify-between gap-2">
              <h3 id="sensor-chart-title" class="text-xs font-bold uppercase tracking-wide text-slate-500">Presión</h3>
              <div role="group" aria-label="Periodo de la gráfica" class="flex rounded-lg bg-slate-200 p-0.5">
                <button
                  v-for="(info, key) in PERIODS"
                  :key="key"
                  type="button"
                  :aria-pressed="period === key"
                  class="h-7 rounded-md px-2.5 text-xs"
                  :class="period === key ? 'bg-white font-bold text-aqua-900 shadow-sm' : 'font-semibold text-slate-600'"
                  @click="period = key"
                >
                  {{ info.text }}
                </button>
              </div>
            </div>
            <p v-if="chartState === 'loading'" class="py-10 text-center text-slate-500">Cargando lecturas…</p>
            <p v-else-if="chartState === 'error'" class="py-10 text-center text-slate-500">No se han podido cargar las lecturas.</p>
            <p v-else-if="!chartReadings.length" class="py-10 text-center text-slate-500">Sin lecturas en este periodo.</p>
            <PressureChart
              v-else
              :readings="chartReadings"
              :min-pressure="sensor.min_pressure"
              :max-pressure="sensor.max_pressure"
              :unit="sensor.unit"
              height="200px"
            />
          </section>

          <dl class="grid grid-cols-[9rem_1fr] gap-x-3 gap-y-2">
            <dt class="text-slate-500">Umbrales</dt>
            <dd class="text-slate-900">{{ formatRange(sensor.min_pressure, sensor.max_pressure, sensor.unit) }}</dd>
            <dt class="text-slate-500">Última lectura</dt>
            <dd class="text-slate-900">
              {{ sensor.last_seen_at ? `${formatDate(sensor.last_seen_at)}, ${formatTime(sensor.last_seen_at)}` : "nunca" }}
            </dd>
            <dt class="text-slate-500">Dado de alta</dt>
            <dd class="text-slate-900">{{ formatDate(sensor.created_at) }}</dd>
            <dt class="text-slate-500">Alertas en 7 días</dt>
            <dd class="text-slate-900">
              {{ alertCount }}
              <router-link
                v-if="alertCount"
                :to="{ name: 'AdminAlerts', query: { q: sensor.external_id } }"
                class="ml-1 font-medium text-aqua-700 hover:underline"
              >
                ver en Alertas
              </router-link>
              <span v-if="alertCount >= TOO_MANY_ALERTS" class="block text-xs font-semibold text-warning-dark">
                Avisa demasiado: revisa los umbrales
              </span>
            </dd>
            <dt class="text-slate-500">Contacto</dt>
            <dd class="text-slate-900">
              <a v-if="contact?.phone" :href="`tel:${contact.phone}`" class="text-aqua-700 hover:underline">{{ contact.phone }}</a>
              <span v-else>—</span>
            </dd>
          </dl>

          <section v-if="recent.length" aria-labelledby="sensor-recent-title" class="flex flex-col gap-2">
            <h3 id="sensor-recent-title" class="text-xs font-bold uppercase tracking-wide text-slate-500">Últimas alertas</h3>
            <ul class="divide-y divide-slate-100 rounded-lg border border-slate-100">
              <li v-for="alert in recent" :key="alert.id" class="flex flex-wrap justify-between gap-x-3 gap-y-0.5 px-3 py-2">
                <span>
                  <b :class="alert.severity === 'CRITICAL' ? 'text-danger-dark' : 'text-warning-dark'">{{ label("AlertType", alert.type) }}</b>
                  <template v-if="alertReading(alert).value"> · {{ alertReading(alert).value }}</template>
                </span>
                <span class="text-slate-500">{{ formatDate(alert.created_at) }} · {{ alertEnd(alert) }}</span>
              </li>
            </ul>
          </section>
        </div>

        <!-- EDIT / CREATE -->
        <form
          v-else
          id="sensor-panel-form"
          novalidate
          class="flex flex-1 flex-col gap-4 px-5 py-5"
          @submit.prevent="submit"
        >
          <label v-if="mode === 'create'" class="flex flex-col gap-1 text-sm font-medium text-slate-700">
            Edificio
            <select
              v-model="siteId"
              class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900"
            >
              <option v-for="option in siteOptions" :key="option.id" :value="option.id">{{ option.label }}</option>
            </select>
          </label>
          <SensorForm
            v-if="site"
            ref="sensorForm"
            v-model="form"
            :floors="site.floors"
            :basements="site.basements"
            :mode="mode"
            :taken-labels="takenLabels"
          />
          <p v-if="error" role="alert" class="rounded-lg bg-danger-light px-3 py-2 text-sm text-danger-dark">{{ error }}</p>
        </form>

        <footer class="border-t border-slate-200 bg-slate-50 px-5 py-4">
          <div v-if="mode === 'detail'" class="grid grid-cols-1">
            <button
              type="button"
              class="h-11 rounded-lg border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-900 hover:border-aqua-400"
              @click="$emit('edit')"
            >
              Ajustar umbrales
            </button>
          </div>
          <div v-else class="grid grid-cols-2 gap-2">
            <button
              type="submit"
              form="sensor-panel-form"
              class="h-11 rounded-lg bg-aqua-600 px-4 text-sm font-bold text-white hover:bg-aqua-700 disabled:opacity-60"
              :disabled="busy || !site"
            >
              {{ busy ? "Guardando…" : "Guardar sensor" }}
            </button>
            <button
              type="button"
              class="h-11 rounded-lg border border-slate-300 bg-white px-4 text-sm font-semibold hover:bg-slate-50"
              :disabled="busy"
              @click="mode === 'create' ? close() : $emit('cancel')"
            >
              Cancelar
            </button>
          </div>
        </footer>
      </aside>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, ref, watch } from "vue";
import PressureChart from "../PressureChart.vue";
import SensorForm, { emptySensor } from "../SensorForm.vue";
import { PERIODS, useAdminSensorsStore } from "../../stores/adminSensors";
import { formatDate, formatPressure, formatRange, formatTime } from "../../composables/useFormat";
import { floorLabel } from "../../utils/floors";
import { alertReading, formatDuration, minutesSince } from "../../utils/alertText";
import { useLabels } from "../../composables/useLabels";
import { isOffline, TOO_MANY_ALERTS } from "../../utils/sensorMaintenance";

const props = defineProps({
  open: { type: Boolean, default: false },
  // detail | edit | create
  mode: { type: String, default: "detail" },
  sensor: { type: Object, default: null },
  // Every building (create: choose one; edit: floors of the sensor's one)
  sites: { type: Array, default: () => [] },
  // Every sensor, for the labels already taken in a building
  sensors: { type: Array, default: () => [] },
  // create: building and floor chosen beforehand ("+ Instalar aquí")
  preset: { type: Object, default: null },
  alertCount: { type: Number, default: 0 },
  contact: { type: Object, default: null },
  busy: { type: Boolean, default: false },
  error: { type: String, default: "" },
});

const emit = defineEmits(["close", "edit", "cancel", "save"]);

const store = useAdminSensorsStore();
const panel = ref(null);
const closeButton = ref(null);
const sensorForm = ref(null);

const { label } = useLabels();
const offline = computed(() => isOffline(props.sensor));

// What the water does, so a working device never looks like "all good"
// next to a red value
const headline = computed(() => {
  const sensor = props.sensor;
  if (sensor?.health === "WARNING" || sensor?.health === "CRITICAL") {
    const high = sensor.last_value > sensor.max_pressure;
    const red = sensor.health === "CRITICAL";
    return {
      text: high ? "Presión alta" : "Presión baja",
      sub: `${high ? "máximo" : "mínimo"} ${formatPressure(high ? sensor.max_pressure : sensor.min_pressure, sensor.unit)} · el aparato funciona`,
      box: red ? "bg-danger-light" : "bg-warning-light",
      title: red ? "text-danger-dark" : "text-warning-dark",
    };
  }
  return {
    text: "Presión normal",
    sub: `normal entre ${formatRange(sensor?.min_pressure, sensor?.max_pressure, sensor?.unit)}`,
    box: offline.value ? "bg-slate-100" : "bg-slate-50",
    title: "text-success-dark",
  };
});

// --- Last alerts ---
const recent = ref([]);

async function loadRecent() {
  recent.value = [];
  if (!props.sensor || props.mode !== "detail") return;
  const id = props.sensor.id;
  try {
    const items = await store.recentAlerts(id);
    if (props.sensor?.id === id) recent.value = items;
  } catch {
    // The section just does not show
  }
}

// "sin atender", "en curso", "se cerró sola" or "cerrada a mano"
function alertEnd(alert) {
  if (alert.state !== "RESOLVED") return label("AlertState", alert.state).toLowerCase();
  return alert.resolved_by_name ? "cerrada a mano" : "se cerró sola";
}
const valueClass = computed(() => {
  if (props.sensor?.health === "CRITICAL") return "text-danger-dark";
  if (props.sensor?.health === "WARNING") return "text-warning-dark";
  return "text-slate-900";
});

function since(value) {
  return formatDuration(minutesSince(value));
}

const ago = computed(() => {
  const minutes = minutesSince(props.sensor?.last_seen_at);
  return minutes < 1 ? "ahora" : `hace ${formatDuration(minutes)}`;
});

// --- Chart ---
const period = ref("24h");
const chartReadings = ref([]);
const chartState = ref("idle");

async function loadChart() {
  if (!props.sensor || props.mode !== "detail") return;
  const id = props.sensor.id;
  chartState.value = "loading";
  try {
    const points = await store.series(id, period.value);
    if (props.sensor?.id !== id) return;
    // PressureChart takes readings: { pressure, measured_at }
    chartReadings.value = points.map((p) => ({ pressure: p.avg, measured_at: p.t }));
    chartState.value = "ok";
  } catch {
    chartState.value = "error";
  }
}

watch(period, loadChart);

// --- Form ---
const form = ref(emptySensor());
const siteId = ref(null);

const siteOptions = computed(() =>
  [...props.sites]
    .sort(
      (a, b) =>
        a.organization_name.localeCompare(b.organization_name, "es") || a.name.localeCompare(b.name, "es"),
    )
    .map((s) => ({ id: s.id, label: `${s.name} · ${s.organization_name}` })),
);

const site = computed(() => props.sites.find((s) => s.id === siteId.value) ?? null);
const takenLabels = computed(() =>
  props.sensors
    .filter((s) => s.site_id === siteId.value && s.id !== props.sensor?.id)
    .map((s) => s.external_id),
);

function resetForm() {
  if (props.mode === "edit" && props.sensor) {
    siteId.value = props.sensor.site_id;
    form.value = {
      name: props.sensor.name,
      floor: props.sensor.floor ?? 0,
      min_pressure: props.sensor.min_pressure,
      max_pressure: props.sensor.max_pressure,
    };
  } else if (props.mode === "create") {
    siteId.value = props.preset?.siteId ?? siteOptions.value[0]?.id ?? null;
    form.value = { ...emptySensor(), floor: props.preset?.floor ?? 0 };
  }
}

function submit() {
  if (!sensorForm.value?.validate()) return;
  emit("save", { mode: props.mode, siteId: siteId.value, data: { ...form.value } });
}

// --- Open, close and focus ---
let opener = null;

watch(
  () => [props.open, props.mode, props.sensor?.id],
  async ([isOpen], [wasOpen] = []) => {
    if (!isOpen) {
      if (wasOpen) opener?.focus?.();
      opener = null;
      return;
    }
    if (!wasOpen) opener = document.activeElement;
    if (props.mode === "detail") {
      period.value = "24h";
      loadChart();
      loadRecent();
    } else {
      resetForm();
    }
    await nextTick();
    closeButton.value?.focus();
  },
);

function close() {
  if (!props.busy) emit("close");
}

function trapFocus(event) {
  const focusable = panel.value?.querySelectorAll(
    'a[href], button:not([disabled]), select, input, [tabindex]:not([tabindex="-1"])',
  );
  if (!focusable?.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}
</script>
