<!--
  PRESSURE SPARKLINE (F24)
  Small pressure chart for a card: the allowed range as a light green band
  and the reading as a line. Plain SVG, no Chart.js: cheap enough for one per
  building card.
  The chart is decorative for screen readers: the card already says the
  pressure in words, so it only carries a short aria-label.
  Usage:
    <PressureSparkline :points="[{ t, avg }]" :min="1.5" :max="6" label="Presión 7 días" />
-->

<template>
  <svg
    :viewBox="`0 0 ${W} ${H}`"
    preserveAspectRatio="none"
    class="h-14 w-full"
    role="img"
    :aria-label="label"
  >
    <!-- Allowed range -->
    <rect
      v-if="band"
      x="0"
      :y="band.y"
      :width="W"
      :height="band.h"
      :fill="chartColors.rangeBand"
    />
    <line
      v-if="band"
      x1="0"
      :x2="W"
      :y1="band.y"
      :y2="band.y"
      :stroke="chartColors.grid"
      stroke-width="1"
      vector-effect="non-scaling-stroke"
    />
    <line
      v-if="band"
      x1="0"
      :x2="W"
      :y1="band.y + band.h"
      :y2="band.y + band.h"
      :stroke="chartColors.grid"
      stroke-width="1"
      vector-effect="non-scaling-stroke"
    />
    <!-- Reading -->
    <polyline
      v-if="path"
      :points="path"
      fill="none"
      :stroke="aqua[600]"
      stroke-width="2"
      stroke-linejoin="round"
      vector-effect="non-scaling-stroke"
    />
  </svg>
</template>

<script setup>
import { computed } from "vue";
import { aqua, chartColors } from "../theme/palette.js";

const props = defineProps({
  // Series points of B7: { t, avg } (min/max per bucket are ignored)
  points: { type: Array, default: () => [] },
  // Allowed range of the sensor
  min: { type: Number, default: null },
  max: { type: Number, default: null },
  label: { type: String, default: "Evolución de la presión" },
});

const W = 200;
const H = 56;
const PAD = 4;

const values = computed(() =>
  props.points.map((p) => p.avg).filter(Number.isFinite),
);

// Vertical scale: covers the readings and the allowed range
const scale = computed(() => {
  const all = [...values.value];
  if (Number.isFinite(props.min)) all.push(props.min);
  if (Number.isFinite(props.max)) all.push(props.max);
  if (!all.length) return null;
  let lo = Math.min(...all);
  let hi = Math.max(...all);
  if (hi === lo) {
    hi += 1;
    lo -= 1;
  }
  return (v) => PAD + ((hi - v) / (hi - lo)) * (H - 2 * PAD);
});

const band = computed(() => {
  if (
    !scale.value ||
    !Number.isFinite(props.min) ||
    !Number.isFinite(props.max)
  )
    return null;
  const top = scale.value(props.max);
  return { y: top, h: scale.value(props.min) - top };
});

const path = computed(() => {
  const v = values.value;
  if (v.length < 2 || !scale.value) return "";
  const step = W / (v.length - 1);
  return v
    .map(
      (value, i) => `${(i * step).toFixed(1)},${scale.value(value).toFixed(1)}`,
    )
    .join(" ");
});
</script>
