<!--
  BUILDING CARD (F24)
  One building on "Mis edificios", answering "is something wrong here?":
    - Name and address.
    - Pending and "en curso" alerts of the building (only when there are any).
    - The sensor to watch (the one with the least margin, see
      utils/pressure.js): its place, the pressure in words with a dot + text,
      the value and its range, and a 7-day sparkline.
    - Sensors and how many are offline.
  The whole card is a button: the parent decides where it opens (today the
  building view in /app?site=<id>, the building page from F25).
  Usage:
    <BuildingCard :site="site" :sensors="sensors" :points="points"
                  :pending="2" @open="openSite" />
-->

<template>
  <button
    type="button"
    class="flex h-full w-full flex-col gap-4 rounded-xl border border-slate-200 bg-white p-5 text-left transition hover:border-aqua-400 hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-aqua-600"
    @click="$emit('open', site.id)"
  >
    <!-- Name -->
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <h2 class="break-words text-lg font-bold text-aqua-900">
          {{ site.name }}
        </h2>
        <p v-if="subtitle" class="text-sm text-slate-600">{{ subtitle }}</p>
      </div>
      <div class="flex shrink-0 flex-col items-end gap-1">
        <span
          v-if="pending > 0"
          class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold"
          :class="toneClasses('danger').pill"
        >
          <span class="h-3.5 w-3.5" aria-hidden="true"
            ><AppIcon name="alert"
          /></span>
          {{ pending }} sin atender
        </span>
        <span
          v-if="inProgress > 0"
          class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold"
          :class="toneClasses('info').pill"
        >
          <span
            class="h-1.5 w-1.5 rounded-full"
            :class="toneClasses('info').dot"
            aria-hidden="true"
          ></span>
          {{ inProgress }} en curso
        </span>
      </div>
    </div>

    <!-- Sensor to watch -->
    <div v-if="watched" class="space-y-2 rounded-lg bg-slate-50 p-3">
      <p class="text-xs font-semibold uppercase text-slate-600">
        {{
          state.key === "ok" ? "Sensor con menos margen" : "Sensor a vigilar"
        }}
      </p>
      <div
        class="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1"
      >
        <p class="font-medium text-slate-900">
          {{ watched.name }}
          <span class="font-normal text-slate-600"
            >· {{ floorLabel(watched.floor) }}</span
          >
        </p>
        <p
          class="flex items-center gap-1.5 text-sm font-semibold text-slate-800"
        >
          <span
            class="h-2 w-2 rounded-full"
            :class="toneClasses(state.tone).dot"
            aria-hidden="true"
          ></span>
          {{ state.text }}
        </p>
      </div>
      <p v-if="state.key !== 'offline'" class="text-sm text-slate-700">
        Ahora {{ formatPressure(watched.last_value, watched.unit) }}
        <span class="text-slate-600"
          >· normal entre
          {{
            formatRange(
              watched.min_pressure,
              watched.max_pressure,
              watched.unit,
            )
          }}</span
        >
      </p>
      <p v-else class="text-sm text-slate-700">
        Última lectura {{ formatDateTime(watched.last_seen_at) }}
      </p>

      <div
        v-if="loadingPoints"
        class="h-14 animate-pulse rounded bg-slate-100"
      ></div>
      <PressureSparkline
        v-else-if="points.length > 1"
        :points="points"
        :min="watched.min_pressure"
        :max="watched.max_pressure"
        :label="`Presión de ${watched.name} en los últimos 7 días`"
      />
      <p v-else class="text-xs text-slate-600">
        Sin lecturas en los últimos 7 días.
      </p>
    </div>
    <p v-else class="rounded-lg bg-slate-50 p-3 text-sm text-slate-600">
      Este edificio todavía no tiene sensores.
    </p>

    <!-- Sensors -->
    <p class="mt-auto text-sm text-slate-700">
      {{ sensors.length }} {{ sensors.length === 1 ? "sensor" : "sensores" }}
      <template v-if="offline > 0">
        · <span class="font-semibold">{{ offline }} sin conexión</span>
      </template>
    </p>
  </button>
</template>

<script setup>
import { computed } from "vue";
import AppIcon from "./AppIcon.vue";
import PressureSparkline from "./PressureSparkline.vue";
import { useLabels } from "../composables/useLabels";
import { useFormat } from "../composables/useFormat";
import { floorLabel } from "../utils/floors.js";
import { pressureState, worstSensor } from "../utils/pressure.js";

const props = defineProps({
  // SiteResponse: id, name, address, building_type
  site: { type: Object, required: true },
  // SensorResponse list of this building
  sensors: { type: Array, default: () => [] },
  // 7-day series of the watched sensor (B7 points: { t, avg })
  points: { type: Array, default: () => [] },
  loadingPoints: { type: Boolean, default: false },
  // Pending alerts (state ACTIVE) of this building
  pending: { type: Number, default: 0 },
  // Alerts somebody is already handling (state ACKNOWLEDGED)
  inProgress: { type: Number, default: 0 },
});

defineEmits(["open"]);

const { label, toneClasses } = useLabels();
const { formatPressure, formatRange, formatDateTime } = useFormat();

const subtitle = computed(
  () => props.site.address || label("BuildingType", props.site.building_type),
);

const watched = computed(() => worstSensor(props.sensors));
const state = computed(() => pressureState(watched.value));
const offline = computed(
  () => props.sensors.filter((s) => pressureState(s).key === "offline").length,
);
</script>
