<!--
  SENSOR DETAIL PANEL (F5, redesigned in F26)
  Detail of the selected sensor next to the building, as in the
  "Plantas y sensores" mockup:
    - Header: name, floor and state. A sensor that does not send shows an
      icon + "Sin conexión" and a sentence saying that zone is not watched.
    - PressureGauge with the value and the pressure in client words
      (utils/pressure.js, the same words as "Mis edificios").
    - Allowed range and last reading (local time).
    - Chart with 24 h · 7 días · 30 días: the same periods as the admin
      sensor panel (PERIODS in stores/adminSensors.js).
    - "Ver alertas de este sensor", with how many it had in 7 days.
  Pure visual component: the parent loads the readings and owns the period.
  Shape: sensor = SensorResponse (B3), readings = { pressure, measured_at }[].
  Usage:
    <SensorDetailPanel
      :sensor="selectedSensor" :readings="readings" :alert-count="3"
      :periods="PERIODS" :period="period" @update:period="period = $event"
      :alerts-to="{ query: { tab: 'alertas', sensor: id } }"
      :loading="loading" :error="error" @retry="loadReadings" />
-->

<template>
  <section
    v-if="sensor"
    class="flex flex-col gap-4 rounded-xl border border-slate-200 bg-white p-5"
    :aria-label="`Detalle del sensor ${sensor.name}`"
  >
    <header class="flex flex-wrap items-start justify-between gap-2">
      <div class="flex min-w-0 flex-col gap-0.5">
        <h2 class="break-words text-lg font-bold text-aqua-900">
          {{ sensor.name }}
        </h2>
        <span class="text-[13px] text-slate-600">{{
          floorLabel(sensor.floor ?? 0)
        }}</span>
      </div>
      <!-- Offline: icon + text, never only a grey dot -->
      <span
        v-if="offline"
        class="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700"
      >
        <span class="h-3.5 w-3.5" aria-hidden="true"
          ><AppIcon name="wifi-off"
        /></span>
        Sin conexión
      </span>
      <StatusPill
        v-else
        type="SensorHealth"
        :value="sensor.health"
        class="shrink-0"
      />
    </header>

    <p
      v-if="offline"
      class="flex items-start gap-2 rounded-lg bg-slate-100 px-3 py-2.5 text-sm text-slate-700"
    >
      <span class="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true"
        ><AppIcon name="wifi-off"
      /></span>
      <span>
        {{ offlineText }} Mientras no envíe datos, esa zona no está vigilada.
      </span>
    </p>

    <div
      class="grid grid-cols-1 gap-2.5 sm:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]"
    >
      <div
        class="flex items-center justify-center rounded-lg bg-slate-50 px-3 py-3 sm:row-span-2"
      >
        <PressureGauge
          :value="sensor.last_value ?? null"
          :min="sensor.min_pressure"
          :max="sensor.max_pressure"
          :unit="unit"
          :tone="state.tone"
          :words="state.text"
          :offline="offline"
        />
      </div>
      <dl class="contents">
        <div
          v-for="item in figures"
          :key="item.label"
          class="flex flex-col justify-center gap-0.5 rounded-lg bg-slate-50 px-3 py-2.5"
        >
          <dt class="text-xs text-slate-600">{{ item.label }}</dt>
          <dd class="text-[17px] font-bold tabular-nums text-aqua-900">
            {{ item.value }}
          </dd>
          <dd v-if="item.sub" class="text-xs text-slate-600">{{ item.sub }}</dd>
        </div>
      </dl>
    </div>

    <figure class="m-0 flex flex-col gap-2">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <figcaption class="text-[13px] font-semibold text-slate-700">
          Presión {{ periodCaption }} ({{ unit }})
        </figcaption>
        <div
          role="group"
          aria-label="Periodo de la gráfica"
          class="flex gap-1"
        >
          <button
            v-for="(info, key) in periods"
            :key="key"
            type="button"
            :aria-pressed="period === key"
            class="h-8 rounded-md px-3 text-xs font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-aqua-600 focus-visible:ring-offset-1"
            :class="
              period === key
                ? 'bg-aqua-600 text-white'
                : 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
            "
            @click="$emit('update:period', key)"
          >
            {{ info.text }}
          </button>
        </div>
      </div>
      <LoadingState v-if="loading" message="Cargando lecturas…" compact />
      <ErrorState
        v-else-if="error"
        :message="error"
        compact
        @retry="$emit('retry')"
      />
      <PressureChart
        v-else
        :readings="readings"
        :min-pressure="sensor.min_pressure"
        :max-pressure="sensor.max_pressure"
        :unit="unit"
      />
    </figure>

    <div
      class="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-600"
    >
      <p>La franja verde es el rango permitido. Toca otro sensor para ver el suyo.</p>
      <RouterLink
        v-if="alertsTo"
        :to="alertsTo"
        class="text-sm font-semibold text-aqua-700 underline underline-offset-2 hover:text-aqua-900"
      >
        Ver alertas de este sensor<template v-if="alertCount"
          > ({{ alertCount }} en 7 días)</template
        >
      </RouterLink>
    </div>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { RouterLink } from "vue-router";
import AppIcon from "./AppIcon.vue";
import StatusPill from "./StatusPill.vue";
import PressureChart from "./PressureChart.vue";
import PressureGauge from "./PressureGauge.vue";
import LoadingState from "./LoadingState.vue";
import ErrorState from "./ErrorState.vue";
import { floorLabel } from "../utils/floors";
import { pressureState } from "../utils/pressure";
import { useFormat } from "../composables/useFormat";

const props = defineProps({
  // SensorResponse (B3); null hides the panel
  sensor: { type: Object, default: null },
  // Points of the chart period: { pressure, measured_at }
  readings: { type: Array, default: () => [] },
  // Alerts of this sensor in the last 7 days; null hides the number
  alertCount: { type: Number, default: null },
  loading: { type: Boolean, default: false },
  // Error message from the parent; shows ErrorState with a retry button
  error: { type: String, default: "" },
  // { key: { days, bucket, text } } and the selected key (update:period)
  periods: { type: Object, required: true },
  period: { type: String, required: true },
  // Route of "Ver alertas de este sensor"; null hides the link
  alertsTo: { type: [Object, String], default: null },
});

defineEmits(["retry", "update:period"]);

const { formatRange, formatRelative, formatDateTime } = useFormat();

const unit = computed(() => props.sensor?.unit || "bar");

// Pressure in client words and its tone (Normal, Algo alta, Demasiado alta…)
const state = computed(() => pressureState(props.sensor));
const offline = computed(() => state.value.key === "offline");

const offlineText = computed(() =>
  props.sensor?.last_seen_at
    ? `Sin lecturas desde ${formatDateTime(props.sensor.last_seen_at)}.`
    : "Este sensor todavía no ha enviado lecturas.",
);

const figures = computed(() => {
  const s = props.sensor;
  if (!s) return [];
  return [
    {
      label: "Rango permitido",
      value: formatRange(s.min_pressure, s.max_pressure, unit.value),
      sub: "Configurado para tu instalación",
    },
    {
      label: "Última lectura",
      value: formatRelative(s.last_seen_at, { empty: "Nunca" }),
      sub: s.last_seen_at ? formatDateTime(s.last_seen_at) : "",
    },
  ];
});

// "de las últimas 24 h" / "de los últimos 7 días"
const periodCaption = computed(() => {
  const info = props.periods[props.period];
  if (!info) return "";
  return info.days === 1
    ? "de las últimas 24 h"
    : `de los últimos ${info.days} días`;
});
</script>
