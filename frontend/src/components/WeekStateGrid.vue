<!--
  WEEK STATE GRID (F25)
  "Tu semana" of the building page: this week (Monday to Sunday, local time)
  per sensor and day.
    - Each cell: how many alerts that sensor had that day, red when any of
      them is still open (Sin atender or En curso), green when all are fixed,
      grey when there were none, dashed for the days still to come. The
      number and the cell's label say it too, never colour alone.
    - Under the grid, the alerts of the week in words with their state.
  Presentational: it receives sensors and alerts and draws them.
  Usage:
    <WeekStateGrid :sensors="sensors" :alerts="alerts" />
-->

<template>
  <div class="space-y-4">
    <div class="overflow-x-auto">
      <div
        class="grid min-w-[270px] items-center gap-1 sm:gap-1.5 text-center text-xs text-slate-600"
        style="
          grid-template-columns: minmax(72px, 150px) repeat(
              7,
              minmax(22px, 1fr)
            );
        "
        role="table"
        aria-label="Avisos de esta semana por sensor y día"
      >
        <div role="row" class="contents">
          <span role="columnheader"><span class="sr-only">Sensor</span></span>
          <span
            v-for="day in days"
            :key="day.key"
            role="columnheader"
            :class="day.isToday ? 'font-bold text-aqua-700' : ''"
          >
            {{ day.short }}<br />{{ day.number }}
          </span>
        </div>

        <div
          v-for="row in rows"
          :key="row.sensor.id"
          role="row"
          class="contents"
        >
          <span role="rowheader" class="min-w-0 text-left text-slate-900">
            <span class="block truncate">{{ row.sensor.name }}</span>
            <span class="block text-slate-600">{{
              floorLabel(row.sensor.floor)
            }}</span>
          </span>
          <span
            v-for="cell in row.cells"
            :key="cell.key"
            role="cell"
            class="flex h-10 items-center justify-center rounded-lg text-sm font-bold"
            :class="cellClass(cell)"
            :aria-label="cell.label"
          >
            {{ cell.count || "" }}
          </span>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <ul class="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600">
      <li class="flex items-center gap-1.5">
        <span class="h-3 w-3 rounded-sm bg-slate-100" aria-hidden="true"></span>
        Sin problemas
      </li>
      <li class="flex items-center gap-1.5">
        <span
          class="h-3 w-3 rounded-sm"
          :class="toneClasses('success').pill"
          aria-hidden="true"
        ></span>
        Hubo un problema, ya arreglado
      </li>
      <li class="flex items-center gap-1.5">
        <span
          class="h-3 w-3 rounded-sm"
          :class="toneClasses('danger').pill"
          aria-hidden="true"
        ></span>
        Problema sin cerrar
      </li>
      <li>El número indica cuántos.</li>
    </ul>

    <!-- The alerts of the week in words -->
    <ul
      v-if="weekAlerts.length"
      class="space-y-2 border-t border-slate-100 pt-3 text-sm"
    >
      <li
        v-for="alert in weekAlerts.slice(0, MAX_ITEMS)"
        :key="alert.id"
        class="flex flex-wrap justify-between gap-x-3 gap-y-0.5"
      >
        <span class="text-slate-900">
          <span class="font-medium">{{ problemText(alert) }}</span>
          <span class="text-slate-600"> · {{ alert.sensor_name }}</span>
        </span>
        <span
          class="flex items-center gap-1.5"
          :class="stateOf(alert).textClass"
        >
          <span
            class="h-2 w-2 rounded-full"
            :class="toneClasses(stateOf(alert).tone).dot"
            aria-hidden="true"
          ></span>
          {{ stateOf(alert).text }}
        </span>
      </li>
    </ul>
    <p v-else class="text-sm text-slate-700">
      Una semana tranquila: ningún aviso en este edificio.
    </p>
    <p v-if="weekAlerts.length > MAX_ITEMS" class="text-sm text-slate-600">
      Y {{ weekAlerts.length - MAX_ITEMS }} más esta semana.
    </p>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useLabels } from "../composables/useLabels";
import { useFormat } from "../composables/useFormat";
import { floorLabel } from "../utils/floors.js";

const props = defineProps({
  // SensorResponse list of the building
  sensors: { type: Array, default: () => [] },
  // AlertResponse list of the building (any state)
  alerts: { type: Array, default: () => [] },
  // For tests; the current moment otherwise
  now: { type: Date, default: null },
});

const MAX_ITEMS = 5;

const { toneClasses } = useLabels();
const { formatRelative } = useFormat();

const PROBLEMS = {
  HIGH_PRESSURE: "Presión demasiado alta",
  LOW_PRESSURE: "Presión demasiado baja",
  SENSOR_OFFLINE: "Sensor sin conexión",
};

function problemText(alert) {
  return PROBLEMS[alert.type] ?? "Problema detectado";
}

// Local day key "2026-10-24"
function dayKey(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

const shortDay = new Intl.DateTimeFormat("es-ES", { weekday: "short" });

// Monday to Sunday of the current week, local time
const days = computed(() => {
  const now = props.now ?? new Date();
  const monday = new Date(now);
  monday.setHours(0, 0, 0, 0);
  monday.setDate(monday.getDate() - ((monday.getDay() + 6) % 7));
  const todayKey = dayKey(now);
  return Array.from({ length: 7 }, (_, i) => {
    const date = new Date(monday);
    date.setDate(monday.getDate() + i);
    const key = dayKey(date);
    const text = shortDay.format(date).replace(".", "");
    return {
      key,
      date,
      short: text.charAt(0).toUpperCase() + text.slice(1),
      number: date.getDate(),
      isToday: key === todayKey,
      isFuture: key > todayKey,
    };
  });
});

const weekStart = computed(() => days.value[0].date.getTime());

function createdDayKey(alert) {
  const date = new Date(alert.created_at);
  return Number.isNaN(date.getTime()) ? null : dayKey(date);
}

// Alerts created this week, newest first
const weekAlerts = computed(() =>
  props.alerts
    .filter((alert) => new Date(alert.created_at).getTime() >= weekStart.value)
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at)),
);

const rows = computed(() =>
  props.sensors.map((sensor) => ({
    sensor,
    cells: days.value.map((day) => {
      const list = weekAlerts.value.filter(
        (alert) =>
          alert.sensor_id === sensor.id && createdDayKey(alert) === day.key,
      );
      const open = list.some((alert) => alert.state !== "RESOLVED");
      const count = list.length;
      let label = `${day.short} ${day.number}: `;
      if (day.isFuture) label += "todavía no ha llegado";
      else if (!count) label += "sin problemas";
      else
        label += `${count} ${count === 1 ? "aviso" : "avisos"}, ${open ? "sin cerrar" : "arreglado"}`;
      return { key: day.key, count, open, isFuture: day.isFuture, label };
    }),
  })),
);

function cellClass(cell) {
  if (cell.isFuture) return "border border-dashed border-slate-200 bg-slate-50";
  if (!cell.count) return "bg-slate-100";
  return cell.open
    ? `${toneClasses("danger").pill} outline outline-1 outline-danger`
    : toneClasses("success").pill;
}

// State of one alert in words
function stateOf(alert) {
  if (alert.state === "RESOLVED") {
    const who = alert.resolved_by_name
      ? ` · lo confirmó ${alert.resolved_by_name}`
      : "";
    return {
      text: `Arreglada${who}`,
      tone: "success",
      textClass: "text-success-dark",
    };
  }
  if (alert.state === "ACKNOWLEDGED")
    return {
      text: `En curso · se encarga ${alert.acknowledged_by_name || "tu equipo"}`,
      tone: "info",
      textClass: "text-info-dark",
    };
  return {
    text: `Sin atender · ${formatRelative(alert.created_at)}`,
    tone: "danger",
    textClass: "text-danger-dark",
  };
}
</script>
