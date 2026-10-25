<!--
  ALERT CLIENT CARDS (#252)
  "Clientes con alertas abiertas": the most urgent clients, each with how many
  alerts are open, a bar (critical / leve over its sensors) and the oldest
  one. Clicking a card filters the table; clicking it again removes the filter.
  The last card says how many more clients have alerts and shows them all.
-->

<template>
  <section aria-labelledby="alert-clients-title" class="flex flex-col gap-3">
    <div class="flex flex-wrap items-baseline justify-between gap-2">
      <h2 id="alert-clients-title" class="text-base font-semibold text-slate-900">
        Clientes con alertas abiertas
        <span class="font-normal text-slate-500">({{ clients.length }})</span>
      </h2>
    </div>

    <p
      v-if="!clients.length"
      class="rounded-xl border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-600"
    >
      Ningún cliente tiene alertas abiertas ahora mismo.
    </p>

    <div v-else class="grid grid-cols-2 gap-3 lg:grid-cols-5">
      <button
        v-for="client in visible"
        :key="client.id"
        type="button"
        :aria-pressed="client.id === selectedId"
        class="flex min-h-[8rem] flex-col gap-2 rounded-xl p-3.5 text-left transition"
        :class="
          client.id === selectedId
            ? 'border-2 border-aqua-600 bg-sky-50'
            : 'border border-slate-200 bg-white hover:border-aqua-400'
        "
        @click="$emit('select', client.id === selectedId ? null : client.id)"
      >
        <span class="w-full truncate font-semibold text-slate-900">
          {{ client.name }}
        </span>
        <span class="flex items-baseline gap-1.5">
          <span
            class="text-3xl font-bold leading-none"
            :class="client.critical_alerts ? 'text-rose-700' : 'text-amber-700'"
          >
            {{ client.open_alerts }}
          </span>
          <span class="text-sm text-slate-700">
            {{ client.open_alerts === 1 ? "abierta" : "abiertas" }}
          </span>
        </span>
        <span
          class="flex h-1.5 overflow-hidden rounded-full bg-teal-100"
          role="img"
          :aria-label="barLabel(client)"
        >
          <span class="bg-rose-700" :style="{ width: share(client.critical_alerts, client) }"></span>
          <span
            class="bg-amber-600"
            :style="{ width: share(client.open_alerts - client.critical_alerts, client) }"
          ></span>
        </span>
        <span class="text-xs text-slate-500">
          de {{ client.sensor_count }} sensores · la más antigua
          {{ oldest(client) }}
        </span>
      </button>

      <button
        v-if="clients.length > max"
        type="button"
        :aria-expanded="expanded"
        class="flex min-h-[8rem] flex-col justify-center gap-1 rounded-xl border border-dashed border-slate-300 p-3.5 text-left text-slate-600 hover:border-aqua-400"
        @click="expanded = !expanded"
      >
        <template v-if="expanded">
          <span class="font-semibold">Ver menos</span>
        </template>
        <template v-else>
          <span class="font-semibold">+ {{ hidden }} clientes</span>
          <span class="text-sm">ver todos</span>
        </template>
      </button>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from "vue";
import { formatDuration, minutesSince } from "../../utils/alertText";

const props = defineProps({
  // OrganizationResponse items with open_alerts > 0, most urgent first
  clients: { type: Array, default: () => [] },
  selectedId: { type: String, default: null },
  // How many cards before "+N clientes"
  max: { type: Number, default: 4 },
});

defineEmits(["select"]);

const expanded = ref(false);
const visible = computed(() =>
  expanded.value ? props.clients : props.clients.slice(0, props.max),
);
const hidden = computed(() => Math.max(0, props.clients.length - props.max));

// Width of a part of the bar. Alerts over sensors: an approximation of how
// much of the client is failing, enough to compare clients at a glance.
function share(count, client) {
  if (!client.sensor_count || count <= 0) return "0%";
  return `${Math.min(100, Math.round((count / client.sensor_count) * 100))}%`;
}

function barLabel(client) {
  const leve = client.open_alerts - client.critical_alerts;
  return `${client.critical_alerts} críticas y ${leve} leves en ${client.sensor_count} sensores`;
}

function oldest(client) {
  return formatDuration(minutesSince(client.oldest_open_alert_at));
}
</script>
