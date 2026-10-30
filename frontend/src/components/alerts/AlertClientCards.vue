<!--
  ALERT CLIENT CARDS (#252)
  "Clientes con alertas abiertas": the most urgent clients, each with how many
  alerts are open, how many are critical / leve, its sensors and the oldest
  one. The cards share the width (3 to 5 per row); on phones they are one
  row that slides sideways, so the alerts are not a screen further down. Clicking a card filters the table; clicking it again removes the filter.
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

    <!-- Phone: one sliding row, to the edges of the screen (-mx-6 px-6 undo
         the p-6 of <main>). From sm: a grid that shares the width. -->
    <div
      v-else
      class="-mx-6 flex snap-x snap-mandatory scroll-px-6 gap-3 overflow-x-auto px-6 pb-2 sm:mx-0 sm:grid sm:grid-cols-[repeat(auto-fit,minmax(14rem,1fr))] sm:overflow-visible sm:px-0 sm:pb-0"
    >
      <button
        v-for="client in visible"
        :key="client.id"
        type="button"
        :aria-pressed="client.id === selectedId"
        class="flex w-60 shrink-0 snap-start flex-col gap-1.5 rounded-xl bg-white px-4 py-3.5 text-left transition sm:w-auto"
        :class="
          client.id === selectedId
            ? 'border-2 border-aqua-600'
            : 'border border-slate-200 hover:border-aqua-400'
        "
        @click="$emit('select', client.id === selectedId ? null : client.id)"
      >
        <span class="w-full truncate font-semibold text-slate-900">
          {{ client.name }}
        </span>
        <span class="flex items-baseline gap-2 whitespace-nowrap">
          <span
            class="text-[1.65rem] font-bold leading-none"
            :class="client.critical_alerts ? 'text-danger-dark' : 'text-warning-dark'"
          >
            {{ client.open_alerts }}
          </span>
          <span class="text-sm text-slate-700">
            {{ client.open_alerts === 1 ? "abierta" : "abiertas" }}
          </span>
        </span>
        <span class="text-sm font-semibold">
          <span v-if="client.critical_alerts" class="text-danger-dark">
            {{ plural(client.critical_alerts, "crítica", "críticas") }}
          </span>
          <template v-if="client.critical_alerts && client.open_alerts - client.critical_alerts"> · </template>
          <span v-if="client.open_alerts - client.critical_alerts" class="text-warning-dark">
            {{ plural(client.open_alerts - client.critical_alerts, "leve", "leves") }}
          </span>
        </span>
        <span class="text-xs text-slate-500">
          {{ plural(client.sensor_count, "sensor", "sensores") }} · la más antigua
          {{ oldest(client) }}
        </span>
      </button>

      <button
        v-if="clients.length > max"
        type="button"
        :aria-expanded="expanded"
        class="flex w-40 shrink-0 snap-start flex-col justify-center gap-1 rounded-xl border border-dashed border-slate-300 px-4 py-3.5 text-left text-slate-600 hover:border-aqua-400 sm:w-auto"
        @click="expanded = !expanded"
      >
        <template v-if="expanded">
          <span class="font-semibold">Ver menos</span>
        </template>
        <template v-else>
          <span class="font-semibold">+ {{ plural(hidden, "cliente", "clientes") }}</span>
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

// '1 sensor', '2 sensores'
function plural(count, one, many) {
  return `${count} ${count === 1 ? one : many}`;
}

function oldest(client) {
  return formatDuration(minutesSince(client.oldest_open_alert_at));
}
</script>
