<!--
  SENSOR CLIENT DETAIL (#283)
  Tab "Sensores", right column (design 3): the chosen client, joined to its
  row in the list. On top the client's name, how many buildings and sensors
  it has, its phone and "Avisar al cliente"; below, every building one after
  the other, each with its title, address, "+ Añadir sensor" and the table
  of its floors from top to bottom (Planta · Sensor · Ahora · Normal entre ·
  Estado). A floor without a sensor says "+ Dar de alta". Clicking a row (or
  Enter on it) opens the side panel. On the phone "‹" goes back to the list
  of clients.
-->

<template>
  <section :aria-labelledby="`client-${client.organizationId}`" class="flex min-w-0 flex-col gap-5">
    <header class="flex flex-wrap items-center gap-x-3 gap-y-2">
      <button
        type="button"
        class="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-white text-xl text-slate-700 lg:hidden"
        aria-label="Volver a los clientes"
        @click="$emit('back')"
      >
        ‹
      </button>
      <div class="min-w-0 flex-1 basis-56">
        <h2 :id="`client-${client.organizationId}`" class="text-2xl font-bold leading-tight text-aqua-800">
          {{ client.organizationName }}
        </h2>
        <p class="mt-0.5 text-sm text-slate-600">
          {{ client.sites.length }} {{ client.sites.length === 1 ? "edificio" : "edificios" }}
          <template v-if="client.counts.sensors">
            · <b class="text-slate-900">{{ client.counts.working }} de {{ client.counts.sensors - client.counts.neverSent }}</b> sensores funcionan
          </template>
          <template v-if="contact?.phone">
            · <a :href="`tel:${contact.phone}`" class="text-aqua-700 underline-offset-2 hover:underline">{{ contact.phone }}</a>
          </template>
        </p>
      </div>
      <a
        v-if="contact?.email"
        :href="mailto"
        class="flex h-10 w-full items-center justify-center rounded-lg border border-slate-300 bg-white px-3.5 text-sm font-semibold text-slate-900 hover:border-aqua-400 sm:w-auto"
      >
        Avisar al cliente
      </a>
    </header>

    <!-- Every building, one after the other: a client has only a few -->
    <section
      v-for="row in client.sites"
      :key="row.site.id"
      :aria-labelledby="`client-site-${row.site.id}`"
      class="flex flex-col gap-2"
    >
      <div class="flex flex-wrap items-center gap-x-3 gap-y-1.5">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="shrink-0 text-slate-600" aria-hidden="true">
          <path d="M4 20V8l8-5 8 5v12" />
          <path d="M9 20v-6h6v6" />
        </svg>
        <h3 :id="`client-site-${row.site.id}`" class="min-w-0 flex-1 text-[17px] font-bold text-slate-900">{{ row.site.name }}</h3>
        <p class="order-last w-full text-[13px] text-slate-600 sm:pl-[30px]">
          <template v-if="row.site.address">{{ row.site.address }} · </template>
          <template v-if="row.counts.sensors">
            {{ row.counts.working }} de {{ row.counts.sensors - row.counts.neverSent }} funcionan<template v-if="row.counts.neverSent"> · {{ row.counts.neverSent }} sin estrenar</template>
          </template>
          <template v-else>todavía sin sensores</template>
          <template v-if="row.total - row.covered">
            · {{ row.total - row.covered }} {{ row.total - row.covered === 1 ? "planta" : "plantas" }} sin sensor
          </template>
        </p>
        <button
          type="button"
          class="h-9 rounded-lg border border-slate-300 bg-white px-3 text-[13px] font-semibold text-aqua-700 hover:border-aqua-400"
          :aria-label="`Añadir sensor en ${row.site.name}`"
          @click="addSensor(row)"
        >
          + Añadir sensor
        </button>
      </div>

      <!-- Phone: every floor in two lines (design A) -->
      <ul class="divide-y divide-slate-100 overflow-hidden rounded-xl border border-slate-200 bg-white sm:hidden">
        <template v-for="f in row.floors" :key="f.floor">
          <li v-if="!f.sensors.length">
            <button
              type="button"
              class="flex min-h-12 w-full items-center justify-between gap-2 bg-slate-50/60 px-4 text-left text-sm"
              @click="install(row, f)"
            >
              <span class="text-slate-600"><b class="text-slate-900">{{ floorLabel(f.floor) }}</b> · sin sensor</span>
              <b class="text-aqua-700">+ Dar de alta</b>
            </button>
          </li>
          <li v-for="sensor in f.sensors" :key="sensor.id">
            <button
              type="button"
              class="grid w-full grid-cols-[minmax(0,1fr)_auto] gap-x-3 gap-y-0.5 px-4 py-3 text-left"
              :class="sensor.id === selectedSensorId ? 'bg-sky-50' : ''"
              @click="$emit('open', sensor)"
            >
              <b class="text-[15px] text-slate-900">{{ floorLabel(f.floor) }}</b>
              <b class="text-right text-[15px]" :class="valueClass(sensor)">
                {{ isOffline(sensor) ? "—" : formatPressure(sensor.last_value, sensor.unit) }}
              </b>
              <span class="truncate text-[13px] text-slate-600">{{ sensor.name }} · {{ sensor.external_id }}</span>
              <span class="justify-self-end whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-bold" :class="status(sensor).class">
                {{ status(sensor).text }}
              </span>
            </button>
          </li>
        </template>
      </ul>

      <div class="relative hidden overflow-x-auto rounded-xl border border-slate-200 bg-white sm:block">
        <table class="w-full min-w-[40rem] text-left text-sm">
          <caption class="sr-only">Plantas de {{ row.site.name }}, de arriba abajo</caption>
          <thead class="whitespace-nowrap text-xs text-slate-500">
            <tr>
              <th scope="col" class="w-28 px-4 py-2.5 font-semibold">Planta</th>
              <th scope="col" class="px-4 py-2.5 font-semibold">Sensor</th>
              <th scope="col" class="w-24 px-4 py-2.5 font-semibold">Ahora</th>
              <th scope="col" class="w-28 px-4 py-2.5 font-semibold">Normal entre</th>
              <th scope="col" class="w-56 px-4 py-2.5 font-semibold">Estado</th>
              <th scope="col" class="w-8 px-2 py-2.5"><span class="sr-only">Abrir</span></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 border-t border-slate-100">
            <template v-for="f in row.floors" :key="f.floor">
              <tr
                v-if="!f.sensors.length"
                tabindex="0"
                class="cursor-pointer bg-slate-50/60 hover:bg-slate-50 focus:bg-sky-50 focus:outline-none"
                :aria-label="`${floorLabel(f.floor)} sin sensor. Dar de alta`"
                @click="install(row, f)"
                @keydown.enter.prevent="install(row, f)"
              >
                <td class="whitespace-nowrap px-4 py-3 font-bold text-slate-900">{{ floorLabel(f.floor) }}</td>
                <td class="px-4 py-3 italic text-slate-500">sin sensor</td>
                <td class="px-4 py-3"></td>
                <td class="px-4 py-3"></td>
                <td class="px-4 py-3 text-[13px] font-bold text-aqua-700">+ Dar de alta</td>
                <td class="px-2 py-3"></td>
              </tr>
              <tr
                v-for="sensor in f.sensors"
                :key="sensor.id"
                tabindex="0"
                class="cursor-pointer focus:outline-none"
                :class="sensor.id === selectedSensorId ? 'bg-sky-50 shadow-[inset_3px_0_0_theme(colors.aqua.600)]' : 'hover:bg-slate-50 focus:bg-sky-50'"
                :aria-current="sensor.id === selectedSensorId ? 'true' : undefined"
                :aria-label="`${floorLabel(f.floor)}, ${sensor.name}. Ver detalle`"
                @click="$emit('open', sensor)"
                @keydown.enter.prevent="$emit('open', sensor)"
              >
                <td class="whitespace-nowrap px-4 py-3 font-bold text-slate-900">{{ floorLabel(f.floor) }}</td>
                <td class="px-4 py-3 text-slate-900">
                  {{ sensor.name }} <span class="text-xs text-slate-500">{{ sensor.external_id }}</span>
                </td>
                <td class="whitespace-nowrap px-4 py-3 font-bold" :class="valueClass(sensor)">
                  {{ isOffline(sensor) ? "—" : formatPressure(sensor.last_value, sensor.unit) }}
                </td>
                <td class="whitespace-nowrap px-4 py-3 text-slate-600">
                  {{ formatNumber(sensor.min_pressure, 1) }} – {{ formatNumber(sensor.max_pressure, 1) }}
                </td>
                <td class="px-4 py-3">
                  <span class="inline-block whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-bold" :class="status(sensor).class">
                    {{ status(sensor).text }}
                  </span>
                </td>
                <td class="px-2 py-3 text-right text-lg text-slate-400" aria-hidden="true">›</td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </section>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { formatNumber, formatPressure } from "../../composables/useFormat";
import { floorLabel } from "../../utils/floors";
import { formatDuration, minutesSince } from "../../utils/alertText";
import { isOffline } from "../../utils/sensorMaintenance";

const props = defineProps({
  // One client of sensorTree(sites, sensors)
  client: { type: Object, required: true },
  selectedSensorId: { type: String, default: null },
  // { sensorId: alerts in the last 7 days }
  alertCounts: { type: Object, default: () => ({}) },
  // { phone, email } of the client
  contact: { type: Object, default: null },
  // Changes on every refresh, so "hace X" is recomputed
  now: { type: Date, default: () => new Date() },
});

const emit = defineEmits(["open", "install", "back"]);

const mailto = computed(() => {
  const subject = `AquaGuard · sensores de ${props.client.organizationName}`;
  return `mailto:${props.contact?.email ?? ""}?subject=${encodeURIComponent(subject)}`;
});

function install(row, f) {
  emit("install", { site: row.site, floor: f.floor });
}

// In this building, on its first floor without a sensor (or the ground floor)
function addSensor(row) {
  const empty = row.floors.find((f) => !f.sensors.length);
  emit("install", { site: row.site, floor: empty?.floor ?? 0 });
}

function valueClass(sensor) {
  if (sensor.health === "CRITICAL") return "text-rose-700";
  if (sensor.health === "WARNING") return "text-amber-700";
  return isOffline(sensor) ? "text-slate-500" : "text-slate-900";
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
</script>
