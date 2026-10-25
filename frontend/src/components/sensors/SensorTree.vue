<!--
  SENSOR TREE (#283)
  Tab "Sensores": every client with its buildings and every floor of each
  building, top to bottom (proposal 1 of the design canvas). A floor shows
  its sensor (a dot, the pressure now and its range) or "Sin sensor ·
  + Dar de alta". Clicking a floor opens the side panel.

  Opens by itself the clients and buildings with something to look at, the
  building of the open sensor and everything when there is only one.
-->

<template>
  <div class="flex flex-col gap-3">
    <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
      <label class="flex items-center gap-2 text-[13px] text-slate-600">
        Ordenar
        <select
          :value="order"
          class="h-9 rounded-lg border border-slate-300 bg-white px-2 text-sm text-slate-900"
          @change="$emit('update:order', $event.target.value)"
        >
          <option value="problems">Con problemas primero</option>
          <option value="az">Cliente A–Z</option>
        </select>
      </label>
      <ul class="flex flex-wrap gap-x-3 gap-y-1 text-[13px] text-slate-600" aria-label="Leyenda">
        <li v-for="item in LEGEND" :key="item.text" class="flex items-center gap-1.5">
          <span class="h-2.5 w-2.5 rounded-full" :class="item.dot" aria-hidden="true"></span>{{ item.text }}
        </li>
      </ul>
    </div>

    <details
      v-for="client in tree"
      :key="client.organizationId"
      :open="openClient(client)"
      class="group/client rounded-xl border border-slate-200 bg-white"
    >
      <summary class="flex cursor-pointer list-none flex-wrap items-center gap-x-3 gap-y-1.5 px-4 py-3.5 sm:px-5 [&::-webkit-details-marker]:hidden">
        <span class="text-slate-500 transition group-open/client:rotate-90" aria-hidden="true">›</span>
        <b class="text-[17px] text-slate-900">{{ client.organizationName }}</b>
        <span class="text-[13px] text-slate-500">
          {{ plural(client.sites.length, "edificio", "edificios") }} ·
          {{ plural(client.floors, "planta", "plantas") }} ·
          {{ plural(client.counts.sensors, "sensor", "sensores") }}
        </span>
        <span class="ml-auto flex flex-wrap gap-1.5">
          <StatusChips :counts="client.counts" />
        </span>
      </summary>

      <div class="flex flex-col gap-2.5 px-3 pb-4 sm:px-5">
        <details
          v-for="row in client.sites"
          :key="row.site.id"
          :open="openSite(client, row)"
          class="group/site rounded-lg border border-slate-100"
        >
          <summary class="flex cursor-pointer list-none flex-wrap items-center gap-x-3 gap-y-1 rounded-lg bg-slate-50 px-3.5 py-2.5 [&::-webkit-details-marker]:hidden">
            <span class="text-slate-500 transition group-open/site:rotate-90" aria-hidden="true">›</span>
            <b class="text-[15px] text-slate-900">{{ row.site.name }}</b>
            <span class="text-[13px] text-slate-500">
              <template v-if="row.site.address">{{ row.site.address }} · </template>{{ row.covered }} de
              {{ plural(row.total, "planta", "plantas") }} con sensor
            </span>
            <span class="ml-auto flex flex-wrap gap-1.5">
              <StatusChips :counts="row.counts" />
            </span>
          </summary>

          <ul class="divide-y divide-slate-100">
            <template v-for="f in row.floors" :key="f.floor">
              <li v-if="!f.sensors.length">
                <button
                  type="button"
                  class="grid w-full grid-cols-[6.5rem_minmax(0,1fr)_auto] items-center gap-3 px-3.5 py-2.5 text-left hover:bg-slate-50"
                  @click="$emit('install', { site: row.site, floor: f.floor })"
                >
                  <b class="text-sm text-slate-900">{{ floorLabel(f.floor) }}</b>
                  <span class="flex items-center gap-2 text-sm text-slate-600">
                    <span class="h-2.5 w-2.5 shrink-0 rounded-full border-2 border-dashed border-slate-400" aria-hidden="true"></span>
                    Sin sensor
                  </span>
                  <span class="text-[13px] font-bold text-aqua-700">+ Dar de alta</span>
                </button>
              </li>
              <li v-for="sensor in f.sensors" :key="sensor.id">
                <button
                  type="button"
                  class="grid w-full grid-cols-[6.5rem_minmax(0,1fr)_auto] items-center gap-x-3 gap-y-0.5 px-3.5 py-2.5 text-left sm:grid-cols-[6.5rem_minmax(0,1fr)_6rem_11rem]"
                  :class="sensor.id === selectedId ? 'bg-sky-50 shadow-[inset_3px_0_0_theme(colors.aqua.600)]' : 'hover:bg-slate-50'"
                  :aria-current="sensor.id === selectedId ? 'true' : undefined"
                  @click="$emit('open', sensor)"
                >
                  <b class="text-sm text-slate-900">{{ floorLabel(f.floor) }}</b>
                  <span class="flex min-w-0 items-center gap-2 text-sm text-slate-900">
                    <span class="h-2.5 w-2.5 shrink-0 rounded-full" :class="DOT[sensor.health] ?? DOT.OK" aria-hidden="true"></span>
                    <span class="truncate">
                      {{ sensor.name }} <span class="text-xs text-slate-500">{{ sensor.external_id }}</span>
                    </span>
                  </span>
                  <b class="text-right text-sm" :class="valueClass(sensor)">
                    {{ isOffline(sensor) ? "—" : formatPressure(sensor.last_value, sensor.unit) }}
                  </b>
                  <span class="col-span-3 text-xs sm:col-span-1 sm:text-right" :class="noteClass(sensor)">{{ note(sensor) }}</span>
                </button>
              </li>
            </template>
          </ul>
        </details>
      </div>
    </details>
  </div>
</template>

<script setup>
import { h } from "vue";
import { formatPressure, formatRange } from "../../composables/useFormat";
import { floorLabel } from "../../utils/floors";
import { formatDuration, minutesSince } from "../../utils/alertText";
import { isOffline } from "../../utils/sensorMaintenance";

const props = defineProps({
  // sensorTree(sites, sensors, order)
  tree: { type: Array, default: () => [] },
  order: { type: String, default: "problems" },
  selectedId: { type: String, default: null },
  // A search or a building filter is on: open everything that is shown
  expandAll: { type: Boolean, default: false },
  // Changes on every refresh, so "hace X" is recomputed
  now: { type: Date, default: () => new Date() },
});

defineEmits(["open", "install", "update:order"]);

const DOT = {
  OK: "bg-emerald-600",
  WARNING: "bg-amber-500",
  CRITICAL: "bg-rose-700",
  OFFLINE: "bg-slate-400",
};

const LEGEND = [
  { text: "funciona", dot: DOT.OK },
  { text: "fuera de rango", dot: DOT.CRITICAL },
  { text: "sin conexión", dot: DOT.OFFLINE },
  { text: "sin sensor", dot: "border-2 border-dashed border-slate-400" },
];

function plural(n, one, many) {
  return `${n} ${n === 1 ? one : many}`;
}

function hasSelected(row) {
  return row.floors.some((f) => f.sensors.some((s) => s.id === props.selectedId));
}

function openClient(client) {
  return (
    props.expandAll ||
    props.tree.length === 1 ||
    client.problems > 0 ||
    client.sites.some(hasSelected)
  );
}

function openSite(client, row) {
  return props.expandAll || client.sites.length === 1 || row.problems > 0 || hasSelected(row);
}

function valueClass(sensor) {
  if (sensor.health === "CRITICAL") return "text-rose-700";
  if (sensor.health === "WARNING") return "text-amber-700";
  return isOffline(sensor) ? "text-slate-500" : "text-slate-900";
}

function note(sensor) {
  if (isOffline(sensor)) {
    if (!sensor.last_seen_at) return "nunca ha enviado";
    return `sin datos hace ${formatDuration(minutesSince(sensor.last_seen_at, props.now))}`;
  }
  if (sensor.health === "WARNING" || sensor.health === "CRITICAL") {
    return sensor.last_value > sensor.max_pressure
      ? `por encima de ${formatPressure(sensor.max_pressure, sensor.unit)}`
      : `por debajo de ${formatPressure(sensor.min_pressure, sensor.unit)}`;
  }
  return `normal ${formatRange(sensor.min_pressure, sensor.max_pressure, sensor.unit)}`;
}

function noteClass(sensor) {
  if (sensor.health === "CRITICAL") return "font-semibold text-rose-700";
  if (sensor.health === "WARNING") return "font-semibold text-amber-700";
  return isOffline(sensor) ? "font-semibold text-slate-600" : "text-slate-500";
}

// "1 fuera de rango", "1 sin conexión" or "todo funciona"
function StatusChips({ counts }) {
  const chips = [];
  if (counts.outOfRange) {
    chips.push(h("span", { class: "rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-bold text-rose-700" }, `${counts.outOfRange} fuera de rango`));
  }
  if (counts.offline) {
    chips.push(h("span", { class: "rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-bold text-slate-600" }, `${counts.offline} sin conexión`));
  }
  if (!chips.length && counts.sensors) {
    chips.push(h("span", { class: "text-[13px] font-semibold text-success-dark" }, "todo funciona"));
  }
  return chips;
}
StatusChips.props = ["counts"];
</script>
