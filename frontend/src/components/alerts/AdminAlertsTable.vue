<!--
  ADMIN ALERTS TABLE (#252)
  Urgencia · Fallo (value and limit) · Cliente / edificio / planta, then two
  columns that depend on the tab, and "›". Clicking a row (or Enter on it)
  opens the detail panel. On small screens each alert is a card.

  | Tab           | Column 4         | Column 5                         |
  | Sin atender   | Quién se ocupa   | Sin atender desde (amber > 1 h)  |
  | En curso      | Quién se ocupa   | Abierta hace                     |
  | Arregladas    | Cómo se cerró    | Tardó                            |
-->

<template>
  <div class="overflow-hidden rounded-xl border border-slate-200 bg-white">
    <!-- Desktop -->
    <table class="hidden w-full text-left text-sm md:table">
      <caption class="sr-only">
        {{ caption }}
      </caption>
      <thead class="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
        <tr>
          <th scope="col" class="px-4 py-2.5 font-semibold">Urgencia</th>
          <th scope="col" class="px-4 py-2.5 font-semibold">Fallo</th>
          <th scope="col" class="px-4 py-2.5 font-semibold">
            Cliente · edificio · planta
          </th>
          <th scope="col" class="px-4 py-2.5 font-semibold">{{ columns[0] }}</th>
          <th scope="col" class="px-4 py-2.5 font-semibold">{{ columns[1] }}</th>
          <th scope="col" class="w-10 px-2 py-2.5"><span class="sr-only">Abrir</span></th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-100">
        <tr
          v-for="alert in rows"
          :key="alert.id"
          tabindex="0"
          class="cursor-pointer align-top hover:bg-slate-50 focus:bg-sky-50 focus:outline-none"
          :class="alert.id === selectedId ? 'bg-sky-50' : ''"
          :aria-label="`${label('AlertType', alert.type)}, ${alert.organization_name}. Ver detalle`"
          @click="$emit('open', alert)"
          @keydown.enter.prevent="$emit('open', alert)"
        >
          <td class="px-4 py-3">
            <span
              class="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-semibold"
              :class="severityClass(alert.severity)"
              :title="help('AlertSeverity', alert.severity)"
            >
              <span class="h-1.5 w-1.5 rounded-full" :class="dotClass(alert.severity)"></span>
              {{ label("AlertSeverity", alert.severity) }}
            </span>
          </td>
          <td class="px-4 py-3">
            <p class="font-medium text-slate-900">{{ label("AlertType", alert.type) }}</p>
            <p v-if="reading(alert).value" class="text-xs text-slate-500">
              <span class="font-semibold text-slate-700">{{ reading(alert).value }}</span>
              <template v-if="reading(alert).limit"> · {{ reading(alert).limit }}</template>
            </p>
            <p v-else class="text-xs text-slate-500">{{ alert.sensor_name }}</p>
          </td>
          <td class="px-4 py-3">
            <p class="font-medium text-slate-900">{{ alert.organization_name }}</p>
            <p class="text-xs text-slate-500">
              {{ alert.site_name }} · {{ floorLabel(alert.floor) }}
            </p>
          </td>
          <td class="px-4 py-3">
            <p :class="cellA(alert).muted ? 'text-slate-500' : 'text-slate-900'">
              {{ cellA(alert).main }}
            </p>
            <p v-if="cellA(alert).sub" class="text-xs text-slate-500">{{ cellA(alert).sub }}</p>
          </td>
          <td class="px-4 py-3">
            <span
              class="inline-flex items-center gap-1"
              :class="cellB(alert).late ? 'font-semibold text-amber-700' : 'text-slate-700'"
            >
              <span v-if="cellB(alert).late" aria-hidden="true">⏱</span>
              {{ cellB(alert).text }}
              <span v-if="cellB(alert).late" class="sr-only">(más de una hora)</span>
            </span>
          </td>
          <td class="px-2 py-3 text-right text-lg text-slate-400" aria-hidden="true">›</td>
        </tr>
      </tbody>
    </table>

    <!-- Mobile -->
    <ul class="divide-y divide-slate-100 md:hidden">
      <li v-for="alert in rows" :key="alert.id">
        <button
          type="button"
          class="flex w-full items-start gap-3 p-4 text-left hover:bg-slate-50"
          @click="$emit('open', alert)"
        >
          <span class="mt-1.5 h-2 w-2 shrink-0 rounded-full" :class="dotClass(alert.severity)"></span>
          <span class="min-w-0 flex-1">
            <span class="block font-medium text-slate-900">
              {{ label("AlertType", alert.type) }}
              <span v-if="reading(alert).value" class="font-normal text-slate-500">
                · {{ reading(alert).value }}
              </span>
            </span>
            <span class="block truncate text-sm text-slate-600">
              {{ alert.organization_name }} · {{ alert.site_name }} ·
              {{ floorLabel(alert.floor) }}
            </span>
            <span
              class="mt-1 block text-xs"
              :class="cellB(alert).late ? 'font-semibold text-amber-700' : 'text-slate-500'"
            >
              {{ columns[1] }}: {{ cellB(alert).text }}
            </span>
          </span>
          <span class="text-lg text-slate-400" aria-hidden="true">›</span>
        </button>
      </li>
    </ul>

    <!-- Pages -->
    <div
      v-if="pages > 1"
      class="flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 px-4 py-2.5 text-sm text-slate-600"
    >
      <span aria-live="polite">
        {{ firstShown }}–{{ lastShown }} de {{ total }}
      </span>
      <span class="flex gap-1">
        <button
          type="button"
          class="rounded-md border border-slate-300 px-3 py-1 disabled:opacity-40"
          :disabled="page <= 1"
          @click="$emit('page', page - 1)"
        >
          Anterior
        </button>
        <button
          type="button"
          class="rounded-md border border-slate-300 px-3 py-1 disabled:opacity-40"
          :disabled="page >= pages"
          @click="$emit('page', page + 1)"
        >
          Siguiente
        </button>
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useLabels } from "../../composables/useLabels";
import { floorLabel } from "../../utils/floors";
import { alertReading, formatDuration, minutesSince } from "../../utils/alertText";

const props = defineProps({
  rows: { type: Array, default: () => [] },
  // ACTIVE | ACKNOWLEDGED | RESOLVED
  state: { type: String, required: true },
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 20 },
  total: { type: Number, default: 0 },
  selectedId: { type: String, default: null },
  // Changes every refresh, so "hace X min" is recomputed
  now: { type: Date, default: () => new Date() },
});

defineEmits(["open", "page"]);

const { label, help } = useLabels();

const COLUMNS = {
  ACTIVE: ["Quién se ocupa", "Sin atender desde"],
  ACKNOWLEDGED: ["Quién se ocupa", "Abierta hace"],
  RESOLVED: ["Cómo se cerró", "Tardó"],
};

const columns = computed(() => COLUMNS[props.state] ?? COLUMNS.ACTIVE);
const caption = computed(() => `Alertas: ${label("AlertState", props.state)}`);

const pages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)));
const firstShown = computed(() => (props.page - 1) * props.pageSize + 1);
const lastShown = computed(() => Math.min(props.total, props.page * props.pageSize));

const reading = alertReading;

function since(value) {
  return formatDuration(minutesSince(value, props.now));
}

// Column 4: who is on it / how it was closed
function cellA(alert) {
  if (props.state === "RESOLVED") {
    return alert.resolved_by_name
      ? { main: alert.resolved_by_name, sub: "a mano" }
      : { main: "Por las lecturas", sub: "volvió a lo normal", muted: true };
  }
  if (props.state === "ACKNOWLEDGED") {
    return {
      main: alert.acknowledged_by_name || "Alguien del cliente",
      sub: alert.acknowledged_at ? `desde hace ${since(alert.acknowledged_at)}` : "",
    };
  }
  return { main: "Nadie", muted: true };
}

// Column 5: how long it has waited / how long it took
function cellB(alert) {
  if (props.state === "RESOLVED") {
    return { text: formatDuration(alert.resolution_minutes) };
  }
  const minutes = minutesSince(alert.created_at, props.now);
  return {
    text: formatDuration(minutes),
    late: props.state === "ACTIVE" && minutes >= 60,
  };
}

function severityClass(severity) {
  return severity === "CRITICAL"
    ? "bg-rose-50 text-rose-700"
    : "bg-amber-50 text-amber-800";
}

function dotClass(severity) {
  return severity === "CRITICAL" ? "bg-rose-700" : "bg-amber-600";
}
</script>
