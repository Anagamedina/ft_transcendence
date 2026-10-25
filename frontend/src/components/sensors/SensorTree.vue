<!--
  SENSOR TREE (#283)
  Tab "Sensores": every client with its buildings and every floor of each
  building, top to bottom: the folding clients and buildings of proposal 1
  with the table of proposal 3 inside each building (Planta · Sensor ·
  Ahora · Normal entre · Estado). A floor without a sensor says "+ Dar de
  alta". Clicking a row (or Enter on it) opens the side panel.

  Opens by itself the clients and buildings with something to look at, the
  building of the open sensor and everything when there is only one.
-->

<template>
  <div class="flex min-w-0 flex-col gap-3">
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
      class="group/client min-w-0 rounded-xl border border-slate-200 bg-white"
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

      <div class="flex min-w-0 flex-col gap-2.5 px-3 pb-4 sm:px-5">
        <details
          v-for="row in client.sites"
          :key="row.site.id"
          :open="openSite(client, row)"
          class="group/site min-w-0 rounded-lg border border-slate-100"
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

          <div class="relative overflow-x-auto">
            <table class="w-full min-w-[40rem] text-left text-sm">
              <caption class="sr-only">Plantas de {{ row.site.name }}</caption>
              <thead class="whitespace-nowrap text-xs text-slate-500">
                <tr>
                  <th scope="col" class="w-28 px-3.5 py-2 font-semibold">Planta</th>
                  <th scope="col" class="px-3.5 py-2 font-semibold">Sensor</th>
                  <th scope="col" class="w-24 px-3.5 py-2 font-semibold">Ahora</th>
                  <th scope="col" class="w-28 px-3.5 py-2 font-semibold">Normal entre</th>
                  <th scope="col" class="w-56 px-3.5 py-2 font-semibold">Estado</th>
                  <th scope="col" class="w-8 px-2 py-2"><span class="sr-only">Abrir</span></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 border-t border-slate-100">
                <template v-for="f in row.floors" :key="f.floor">
                  <tr
                    v-if="!f.sensors.length"
                    tabindex="0"
                    class="cursor-pointer hover:bg-slate-50 focus:bg-sky-50 focus:outline-none"
                    :aria-label="`${floorLabel(f.floor)} sin sensor. Dar de alta`"
                    @click="install(row, f)"
                    @keydown.enter.prevent="install(row, f)"
                  >
                    <td class="whitespace-nowrap px-3.5 py-2.5 font-bold text-slate-900">{{ floorLabel(f.floor) }}</td>
                    <td class="px-3.5 py-2.5 italic text-slate-500">sin sensor</td>
                    <td class="px-3.5 py-2.5"></td>
                    <td class="px-3.5 py-2.5"></td>
                    <td class="px-3.5 py-2.5 text-[13px] font-bold text-aqua-700">+ Dar de alta</td>
                    <td class="px-2 py-2.5"></td>
                  </tr>
                  <tr
                    v-for="sensor in f.sensors"
                    :key="sensor.id"
                    tabindex="0"
                    class="cursor-pointer focus:outline-none"
                    :class="sensor.id === selectedId ? 'bg-sky-50 shadow-[inset_3px_0_0_theme(colors.aqua.600)]' : 'hover:bg-slate-50 focus:bg-sky-50'"
                    :aria-current="sensor.id === selectedId ? 'true' : undefined"
                    :aria-label="`${floorLabel(f.floor)}, ${sensor.name}. Ver detalle`"
                    @click="$emit('open', sensor)"
                    @keydown.enter.prevent="$emit('open', sensor)"
                  >
                    <td class="whitespace-nowrap px-3.5 py-2.5 font-bold text-slate-900">{{ floorLabel(f.floor) }}</td>
                    <td class="px-3.5 py-2.5 text-slate-900">
                      {{ sensor.name }} <span class="text-xs text-slate-500">{{ sensor.external_id }}</span>
                    </td>
                    <td class="whitespace-nowrap px-3.5 py-2.5 font-bold" :class="valueClass(sensor)">
                      {{ isOffline(sensor) ? "—" : formatPressure(sensor.last_value, sensor.unit) }}
                    </td>
                    <td class="whitespace-nowrap px-3.5 py-2.5 text-slate-600">
                      {{ formatNumber(sensor.min_pressure, 1) }} – {{ formatNumber(sensor.max_pressure, 1) }}
                    </td>
                    <td class="px-3.5 py-2.5">
                      <span class="inline-block whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-bold" :class="status(sensor).class">
                        {{ status(sensor).text }}
                      </span>
                    </td>
                    <td class="px-2 py-2.5 text-right text-lg text-slate-400" aria-hidden="true">›</td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </details>
      </div>
    </details>
  </div>
</template>

<script setup>
import { h } from "vue";
import { formatNumber, formatPressure } from "../../composables/useFormat";
import { floorLabel } from "../../utils/floors";
import { formatDuration, minutesSince } from "../../utils/alertText";
import { isOffline } from "../../utils/sensorMaintenance";

const props = defineProps({
  // sensorTree(sites, sensors, order)
  tree: { type: Array, default: () => [] },
  order: { type: String, default: "problems" },
  selectedId: { type: String, default: null },
  // { sensorId: alerts in the last 7 days }
  alertCounts: { type: Object, default: () => ({}) },
  // A search or a building filter is on: open everything that is shown
  expandAll: { type: Boolean, default: false },
  // Changes on every refresh, so "hace X" is recomputed
  now: { type: Date, default: () => new Date() },
});

const emit = defineEmits(["open", "install", "update:order"]);

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

function install(row, f) {
  emit("install", { site: row.site, floor: f.floor });
}

// The Estado column: what is wrong, or "funciona"
function status(sensor) {
  if (isOffline(sensor)) {
    if (!sensor.last_seen_at) return { text: "nunca ha enviado", class: "bg-slate-50 text-slate-500" };
    return {
      text: `sin conexión · ${formatDuration(minutesSince(sensor.last_seen_at, props.now))}`,
      class: "bg-slate-100 text-slate-700",
    };
  }
  if (sensor.health === "WARNING" || sensor.health === "CRITICAL") {
    const side = sensor.last_value > sensor.max_pressure ? "alta" : "baja";
    const alerts = props.alertCounts[sensor.id] ?? 0;
    return {
      text: alerts ? `${side} · ${alerts} ${alerts === 1 ? "alerta" : "alertas"} en 7 días` : side,
      class: sensor.health === "CRITICAL" ? "bg-rose-50 text-rose-700" : "bg-amber-50 text-amber-800",
    };
  }
  return { text: "funciona", class: "bg-emerald-50 text-success-dark" };
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
