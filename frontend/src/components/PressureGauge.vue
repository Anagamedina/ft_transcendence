<!--
  PRESSURE GAUGE (F26)
  Half-circle gauge for one sensor, as in the "Plantas y sensores" mockup:
    - grey track, green band for the allowed range (min..max),
    - a needle on the current value, coloured by state,
    - below: the value and the pressure in client words.
  The colour is never the only signal: the value and the words are text,
  and the SVG has a full text alternative (role="img" + aria-label).
  Colours come from theme/palette.js (SVG needs plain hex values).
  Usage:
    <PressureGauge :value="6.8" :min="1.5" :max="6" unit="bar"
                   tone="danger" words="Demasiado alta" />
    <PressureGauge :value="3.1" :min="1.5" :max="8" offline words="Sin conexión" />
-->

<template>
  <figure class="m-0 flex flex-col items-center">
    <svg
      viewBox="0 0 200 116"
      class="w-full max-w-[220px]"
      role="img"
      :aria-label="description"
    >
      <!-- Track: the whole scale -->
      <path
        :d="arc(0, 1)"
        fill="none"
        :stroke="chartColors.grid"
        stroke-width="14"
        stroke-linecap="round"
      />
      <!-- Allowed range -->
      <path
        v-if="band"
        :d="arc(band[0], band[1])"
        fill="none"
        :stroke="offline ? chartColors.ink : status.success.DEFAULT"
        :stroke-opacity="offline ? 0.35 : 1"
        stroke-width="14"
      />
      <!-- Needle -->
      <g v-if="needle">
        <line
          :x1="CX"
          :y1="CY"
          :x2="needle.x"
          :y2="needle.y"
          :stroke="needleColor"
          stroke-width="4"
          stroke-linecap="round"
        />
        <circle :cx="CX" :cy="CY" r="7" :fill="needleColor" />
      </g>
      <!-- Limits under the ends of the band -->
      <text
        v-if="band"
        :x="limitX(band[0])"
        y="114"
        text-anchor="middle"
        class="fill-slate-600 text-[11px]"
      >
        {{ formatNumber(min) }}
      </text>
      <text
        v-if="band"
        :x="limitX(band[1])"
        y="114"
        text-anchor="middle"
        class="fill-slate-600 text-[11px]"
      >
        {{ formatNumber(max) }}
      </text>
    </svg>

    <figcaption class="mt-1 flex flex-col items-center gap-0.5 text-center">
      <span
        class="text-2xl font-bold tabular-nums"
        :class="offline ? 'text-slate-700' : valueClass"
      >
        {{ hasValue ? formatPressure(value, unit) : "—" }}
      </span>
      <span class="text-sm font-semibold" :class="offline ? 'text-slate-700' : valueClass">
        {{ words }}
      </span>
      <span v-if="offline && hasValue" class="text-xs text-slate-600">
        Última lectura recibida
      </span>
    </figcaption>
  </figure>
</template>

<script setup>
import { computed } from "vue";
import { status, chartColors } from "../theme/palette.js";
import { useFormat } from "../composables/useFormat";

const props = defineProps({
  // Current (or last) reading; null when the sensor never sent one
  value: { type: Number, default: null },
  // Allowed range of the sensor
  min: { type: Number, required: true },
  max: { type: Number, required: true },
  unit: { type: String, default: "bar" },
  // useLabels tone of the state: success | warning | danger | neutral
  tone: { type: String, default: "neutral" },
  // Pressure in client words ("Normal", "Demasiado alta"…)
  words: { type: String, default: "" },
  // Sensor not sending: grey gauge, needle on the last value
  offline: { type: Boolean, default: false },
});

const { formatPressure } = useFormat();

// Geometry: centre at the bottom middle, radius 80
const CX = 100;
const CY = 100;
const R = 80;

const hasValue = computed(() => Number.isFinite(props.value));
const validRange = computed(
  () =>
    Number.isFinite(props.min) &&
    Number.isFinite(props.max) &&
    props.max > props.min,
);

// Scale: the allowed range in the middle, half a range of margin each side,
// stretched if the reading is further out (never below 0)
const scale = computed(() => {
  if (!validRange.value) return null;
  const span = props.max - props.min;
  let low = Math.max(0, props.min - span / 2);
  let high = props.max + span / 2;
  if (hasValue.value) {
    low = Math.min(low, props.value);
    high = Math.max(high, props.value);
  }
  return { low, high };
});

// 0..1 position of a pressure on the scale
function fraction(pressure) {
  const { low, high } = scale.value;
  return Math.min(1, Math.max(0, (pressure - low) / (high - low)));
}

// Point on the arc: 0 = left end, 1 = right end
function point(f, radius = R) {
  const angle = Math.PI * (1 - f);
  return { x: CX + radius * Math.cos(angle), y: CY - radius * Math.sin(angle) };
}

// SVG path of the arc between two fractions (always under 180°)
function arc(from, to) {
  const a = point(from);
  const b = point(to);
  return `M ${a.x.toFixed(2)} ${a.y.toFixed(2)} A ${R} ${R} 0 0 1 ${b.x.toFixed(2)} ${b.y.toFixed(2)}`;
}

const band = computed(() =>
  scale.value ? [fraction(props.min), fraction(props.max)] : null,
);

// Labels sit just outside the arc, under each end of the band
function limitX(f) {
  return Math.min(188, Math.max(12, point(f, R + 4).x));
}

const needle = computed(() =>
  scale.value && hasValue.value ? point(fraction(props.value), R - 14) : null,
);

// Dark shade of the state: AA on white, also for the needle
const TONE_HEX = {
  success: status.success.dark,
  warning: status.warning.dark,
  danger: status.danger.dark,
  info: status.info.dark,
};
const needleColor = computed(() =>
  props.offline ? chartColors.ink : (TONE_HEX[props.tone] ?? chartColors.ink),
);

// Text colour of the value: same dark shade as the pills (AA on white)
const TONE_TEXT = {
  success: "text-success-dark",
  warning: "text-warning-dark",
  danger: "text-danger-dark",
  info: "text-info-dark",
};
const valueClass = computed(() => TONE_TEXT[props.tone] ?? "text-slate-900");

// "1,5" (no unit) for the limits
function formatNumber(n) {
  return Number.isFinite(n)
    ? n.toLocaleString("es-ES", { maximumFractionDigits: 1, minimumFractionDigits: 1 })
    : "";
}

const description = computed(() => {
  const range = validRange.value
    ? `rango permitido de ${formatNumber(props.min)} a ${formatNumber(props.max)} ${props.unit}`
    : "sin rango configurado";
  if (!hasValue.value) return `Medidor de presión: sin lecturas, ${range}.`;
  const value = formatPressure(props.value, props.unit);
  const state = props.offline ? "sin conexión, última lectura" : props.words;
  return `Medidor de presión: ${value}, ${state}; ${range}.`;
});
</script>
