<!--
  ADMIN ALERTS TABLE (#252)
  Urgencia · Fallo (value and limit) · Cliente / edificio / planta (only
  edificio / planta when one client is filtered), then the columns of the
  tab, and "›". Clicking a row (or Enter on it) opens the detail panel.
  From 1152 px (a laptop with 125 % zoom is ~1229; measured: "Sin atender",
  the widest tab, fits from 1152) it is a table; under xl it is tighter and
  "Urgencia" becomes a dot before the fault, so it fits next to the side
  menu. Narrower, each alert is a card, with the notices line too.

  | Tab           | Column 4         | Column 5                         |
  | Sin atender   | Avisos al cliente (#275; no column until the backend sends them) | Sin atender desde (amber > 1 h) |
  | En curso      | Quién se ocupa   | Abierta hace                     |
  | Arregladas    | Cómo se cerró    | Tardó                            |
-->

<template>
  <div class="overflow-hidden rounded-xl border border-slate-200 bg-white">
    <!-- Desktop -->
    <table class="hidden w-full text-left text-sm min-[1152px]:table">
      <caption class="sr-only">
        {{ caption }}
      </caption>
      <thead class="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
        <tr>
          <th scope="col" class="hidden w-28 px-4 py-2.5 font-semibold xl:table-cell">Urgencia</th>
          <th scope="col" class="px-3 py-2.5 font-semibold xl:w-64 xl:px-4">Fallo</th>
          <th scope="col" class="px-3 py-2.5 font-semibold xl:px-4">
            {{ clientFiltered ? "Edificio · planta" : "Cliente · edificio · planta" }}
          </th>
          <th v-if="columns[0]" scope="col" class="px-3 py-2.5 font-semibold xl:px-4">{{ columns[0] }}</th>
          <th scope="col" class="px-3 py-2.5 font-semibold xl:px-4">{{ columns[1] }}</th>
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
          <td class="hidden px-4 py-3 xl:table-cell">
            <span
              class="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-semibold"
              :class="severityClass(alert.severity)"
              :title="help('AlertSeverity', alert.severity)"
            >
              <span class="h-1.5 w-1.5 rounded-full" :class="dotClass(alert.severity)"></span>
              {{ label("AlertSeverity", alert.severity) }}
            </span>
          </td>
          <td class="px-3 py-3 xl:px-4">
            <p class="flex items-center gap-2 whitespace-nowrap font-medium text-slate-900">
              <span
                class="h-2 w-2 shrink-0 rounded-full xl:hidden"
                :class="dotClass(alert.severity)"
                :title="label('AlertSeverity', alert.severity)"
                aria-hidden="true"
              ></span>
              <span class="sr-only xl:hidden">{{ label("AlertSeverity", alert.severity) }}:</span>
              {{ label("AlertType", alert.type) }}
            </p>
            <p v-if="reading(alert).value" class="text-xs text-slate-500">
              <span class="font-semibold text-slate-700">{{ reading(alert).value }}</span>
              <template v-if="reading(alert).limit"> · {{ reading(alert).limit }}</template>
            </p>
            <p v-else class="text-xs text-slate-500">{{ alert.sensor_name }}</p>
          </td>
          <td v-if="clientFiltered" class="px-3 py-3 xl:px-4">
            <p class="font-medium text-slate-900">{{ alert.site_name }}</p>
            <p class="text-xs text-slate-500">{{ floorLabel(alert.floor) }}</p>
          </td>
          <td v-else class="px-3 py-3 xl:px-4">
            <p class="font-medium text-slate-900">{{ alert.organization_name }}</p>
            <p class="text-xs text-slate-500">
              {{ alert.site_name }} · {{ floorLabel(alert.floor) }}
            </p>
          </td>
          <td v-if="notice(alert)" class="px-3 py-3 xl:px-4">
            <p class="flex items-center gap-1.5" :class="NOTICE_TEXT[notice(alert).tone ?? 'none']">
              <svg
                v-if="notice(alert).tone === 'call'"
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                aria-hidden="true"
              >
                <path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2" />
              </svg>
              {{ notice(alert).main }}
            </p>
            <p v-if="notice(alert).sub" class="text-xs text-slate-500">{{ notice(alert).sub }}</p>
          </td>
          <td v-else-if="columns[0]" class="px-3 py-3 xl:px-4">
            <p :class="cellA(alert).muted ? 'text-slate-500' : 'text-slate-900'">
              {{ cellA(alert).main }}
            </p>
            <p v-if="cellA(alert).sub" class="text-xs text-slate-500">{{ cellA(alert).sub }}</p>
          </td>
          <td class="px-3 py-3 xl:px-4">
            <span
              class="inline-flex items-center gap-1.5 whitespace-nowrap"
              :class="cellB(alert).late ? 'font-semibold text-amber-700' : 'text-slate-700'"
            >
              <svg
                v-if="cellB(alert).late"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                aria-hidden="true"
              >
                <circle cx="12" cy="13" r="8" />
                <path d="M12 9v4l2.5 2.5M9 2h6" />
              </svg>
              {{ cellB(alert).text }}
              <span v-if="cellB(alert).late" class="sr-only">(más de una hora)</span>
            </span>
          </td>
          <td class="px-2 py-3 text-right text-lg text-slate-400" aria-hidden="true">›</td>
        </tr>
      </tbody>
    </table>

    <!-- Phone and tablet -->
    <ul class="divide-y divide-slate-100 min-[1152px]:hidden">
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
            <span class="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-xs">
              <span :class="cellB(alert).late ? 'font-semibold text-amber-700' : 'text-slate-500'">
                {{ columns[1] }}: {{ cellB(alert).text }}
              </span>
              <span v-if="notice(alert)" :class="NOTICE_TEXT[notice(alert).tone ?? 'none']">
                {{ notice(alert).main }}<template v-if="notice(alert).sub"> · {{ notice(alert).sub }}</template>
              </span>
              <span v-else-if="columns[0]" class="text-slate-500">
                {{ cellA(alert).main }}<template v-if="cellA(alert).sub"> · {{ cellA(alert).sub }}</template>
              </span>
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
import { noticeSummary } from "../../utils/notificationSteps";

const props = defineProps({
  rows: { type: Array, default: () => [] },
  // ACTIVE | ACKNOWLEDGED | RESOLVED
  state: { type: String, required: true },
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 20 },
  total: { type: Number, default: 0 },
  selectedId: { type: String, default: null },
  // One client chosen in the filters: its name would repeat on every row
  clientFiltered: { type: Boolean, default: false },
  // Changes every refresh, so "hace X min" is recomputed
  now: { type: Date, default: () => new Date() },
});

defineEmits(["open", "page"]);

const { label, help } = useLabels();

const COLUMNS = {
  // "Quién se ocupa" would always say "Nadie" here: no column until #275
  ACTIVE: [null, "Sin atender desde"],
  ACKNOWLEDGED: ["Quién se ocupa", "Abierta hace"],
  RESOLVED: ["Cómo se cerró", "Tardó"],
};

// "Avisos al cliente" appears in "Sin atender" once the backend sends the
// notices (#275)
const columns = computed(() => {
  const base = COLUMNS[props.state] ?? COLUMNS.ACTIVE;
  const withNotices =
    props.state === "ACTIVE" && props.rows.some((a) => Array.isArray(a.notifications));
  return withNotices ? ["Avisos al cliente", base[1]] : base;
});

// Amber like the "late" clock: it waits too long. Red is only for "Crítica"
const NOTICE_TEXT = {
  call: "font-semibold text-amber-700",
  sent: "font-medium text-slate-700",
  normal: "font-medium text-success-dark",
  none: "text-slate-500",
};

function notice(alert) {
  return props.state === "ACTIVE" ? noticeSummary(alert, props.now) : null;
}
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
