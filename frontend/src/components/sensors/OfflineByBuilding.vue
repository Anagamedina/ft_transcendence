<!--
  OFFLINE BY BUILDING (#283)
  Tab "Sin conexión". On top, the sensors that stopped sending (a failure
  to tell the client about), one card per building with the longest silence
  first: how urgent it is ("más de 6 h"), "Avisar al cliente" (an email
  already written) and each sensor with the time of its last reading. Below, folded,
  the sensors that never sent anything: installation not finished, not a
  failure. The admin does not go to the building: they tell the client.
-->

<template>
  <div class="flex flex-col gap-4">
    <section v-if="groups.length" aria-labelledby="offline-stopped-title" class="flex flex-col gap-3">
      <h2 id="offline-stopped-title" class="text-[15px] font-bold text-slate-700">
        Dejaron de enviar
        <span class="font-normal text-slate-500">· avisa al cliente para que lo revise</span>
      </h2>

      <article
        v-for="group in groups"
        :key="group.siteId"
        class="overflow-hidden rounded-xl border border-slate-200 bg-white"
      >
        <header class="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-slate-100 px-4 py-3.5 sm:px-5">
          <div class="min-w-[14rem] flex-1">
            <h3 class="text-base font-bold text-slate-900">{{ group.siteName }}</h3>
            <p class="text-[13px] text-slate-500">
              {{ group.organizationName }}
              <template v-if="group.sensors.length > 1">
                · <b class="text-amber-700">{{ group.sensors.length }} sensores a la vez: puede ser la wifi del edificio</b>
              </template>
            </p>
          </div>
          <span
            v-if="badge(group)"
            class="rounded-full px-2.5 py-0.5 text-[13px] font-bold"
            :class="badge(group).tone === 'red' ? 'bg-rose-50 text-rose-700' : 'bg-amber-50 text-amber-700'"
          >
            {{ badge(group).text }}
          </span>
          <a
            :href="mailto(group)"
            class="flex h-10 items-center rounded-lg bg-aqua-600 px-4 text-sm font-bold text-white hover:bg-aqua-700"
          >
            Avisar al cliente
          </a>
        </header>

        <ul class="divide-y divide-slate-50">
          <li v-for="sensor in group.sensors" :key="sensor.id">
            <button
              type="button"
              class="grid w-full grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-1 px-4 py-3 text-left hover:bg-slate-50 sm:grid-cols-[minmax(0,1fr)_16rem_10rem_1rem] sm:px-5"
              :class="sensor.id === selectedId ? 'bg-sky-50' : ''"
              @click="$emit('open', sensor)"
            >
              <span>
                <b class="text-sm text-slate-900">{{ sensor.name }}</b>
                <span class="block text-xs text-slate-500">{{ floorLabel(sensor.floor ?? 0) }} · {{ sensor.external_id }}</span>
              </span>
              <span class="col-span-2 row-start-2 text-[13px] text-slate-600 sm:col-span-1 sm:row-start-auto">
                Última lectura {{ lastDay(sensor) }} a las <b class="text-slate-900">{{ formatTime(sensor.last_seen_at) }}</b>
                <span class="block text-xs text-slate-500">marcaba {{ formatPressure(sensor.last_value, sensor.unit) }}</span>
              </span>
              <span class="text-right">
                <span class="block text-xs text-slate-500">sin lecturas</span>
                <b class="text-[15px]" :class="minutes(sensor) >= 360 ? 'text-rose-700' : 'text-amber-700'">
                  hace {{ formatDuration(minutes(sensor)) }}
                </b>
              </span>
              <span class="hidden text-slate-400 sm:block" aria-hidden="true">›</span>
            </button>
          </li>
        </ul>
      </article>
    </section>

    <p
      v-else
      class="rounded-xl border border-emerald-200 bg-emerald-50 p-8 text-center font-semibold text-emerald-800"
    >
      ✓ Todos los sensores conectados envían lecturas
    </p>

    <details v-if="never.length" class="rounded-xl border border-dashed border-slate-300 bg-white px-4 py-3.5 sm:px-5">
      <summary class="cursor-pointer text-[15px] font-bold text-slate-700">
        {{ never.length }} {{ never.length === 1 ? "sensor que nunca ha enviado" : "sensores que nunca han enviado" }}
        <span class="font-normal text-slate-500">· dados de alta pero sin conectar todavía: no es una avería</span>
      </summary>
      <ul class="mt-3 divide-y divide-slate-100">
        <li v-for="sensor in never" :key="sensor.id">
          <button type="button" class="w-full py-2.5 text-left text-sm hover:bg-slate-50" @click="$emit('open', sensor)">
            <b class="text-slate-900">{{ sensor.name }}</b>
            <span class="text-slate-500"> · {{ sensor.organization_name }} · {{ sensor.site_name }} · {{ floorLabel(sensor.floor ?? 0) }}</span>
          </button>
        </li>
      </ul>
    </details>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { formatPressure, formatTime } from "../../composables/useFormat";
import { floorLabel } from "../../utils/floors";
import { formatDuration, minutesSince } from "../../utils/alertText";
import { groupBySite, noticeMailto, silenceBadge } from "../../utils/sensorMaintenance";

const props = defineProps({
  // Sensors that stopped sending (they have last_seen_at)
  stopped: { type: Array, default: () => [] },
  // Sensors that never sent anything
  never: { type: Array, default: () => [] },
  // { organizationId: { phone, email } }
  contacts: { type: Object, default: () => ({}) },
  selectedId: { type: String, default: null },
  // Changes on every refresh, so "hace X" is recomputed
  now: { type: Date, default: () => new Date() },
});

defineEmits(["open"]);

const groups = computed(() => groupBySite(props.stopped));

function minutes(sensor) {
  return minutesSince(sensor.last_seen_at, props.now) ?? 0;
}

function badge(group) {
  return silenceBadge(minutes(group.sensors[0]));
}

// "hoy", "ayer" or the date
function lastDay(sensor) {
  const seen = new Date(sensor.last_seen_at);
  const days = Math.round((startOfDay(props.now) - startOfDay(seen)) / 86400000);
  if (days === 0) return "hoy";
  if (days === 1) return "ayer";
  return `el ${seen.toLocaleDateString("es-ES", { day: "numeric", month: "numeric" })}`;
}

function startOfDay(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}

function mailto(group) {
  const email = props.contacts[group.organizationId]?.email;
  return noticeMailto(email, group, formatDuration(minutes(group.sensors[0])));
}
</script>
