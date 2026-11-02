<!--
  SENSOR CLIENT LIST (#283)
  Tab "Sensores", left column (design 3): every client in one row, on grey,
  in two groups. "Necesitan atención" on top, each with an icon (amber
  triangle: the pressure; grey wifi: no connection), what is wrong in a few
  words and how many of its sensors work (one that never sent is not
  counted: it is "sin estrenar"). "Funcionan bien" below, quieter, by name.
  The chosen client is white and touches the right edge, so it joins its
  card on the right like a folder tab. The list scrolls inside its column.
-->

<template>
  <nav aria-label="Clientes" class="flex flex-col gap-1 py-3 pl-3 lg:max-h-[48rem] lg:overflow-y-auto">
    <template v-if="needAttention.length">
      <h2 class="mb-0.5 ml-1 mr-3 mt-1 text-xs font-extrabold uppercase tracking-wide text-warning-dark">
        Necesitan atención · {{ needAttention.length }}
      </h2>
      <ul class="flex flex-col gap-0.5">
        <li v-for="client in needAttention" :key="client.organizationId">
          <button
            type="button"
            class="flex min-h-14 items-center gap-2.5 px-3 py-2 text-left"
            :class="rowClass(client)"
            :aria-current="client.organizationId === selectedId ? 'true' : undefined"
            @click="$emit('select', client.organizationId)"
          >
            <span
              class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
              :class="issue(client).kind === 'pressure' ? 'bg-warning-light text-warning-dark' : 'bg-slate-200 text-slate-600'"
              aria-hidden="true"
            >
              <svg v-if="issue(client).kind === 'pressure'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                <path d="M12 4 2.5 20h19z" />
                <path d="M12 10v4M12 17h.01" />
              </svg>
              <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                <path d="M2 8.8a15 15 0 0 1 20 0M5 12.5a10 10 0 0 1 14 0M8.5 16.4a5 5 0 0 1 7 0" />
                <path d="m3 3 18 18" />
              </svg>
            </span>
            <span class="flex min-w-0 flex-1 flex-col">
              <b class="truncate text-sm" :class="client.organizationId === selectedId ? 'text-aqua-800' : 'text-slate-900'">
                {{ client.organizationName }}
              </b>
              <span class="text-xs text-slate-600">{{ issueText(client) }}</span>
            </span>
            <span class="flex shrink-0 flex-col items-end text-xs leading-tight text-slate-600">
              <b class="text-sm text-slate-900">{{ client.counts.working }} de {{ client.counts.sensors - client.counts.neverSent }}</b>
              funcionan
            </span>
          </button>
        </li>
      </ul>
    </template>

    <template v-if="allGood.length">
      <h2
        class="mb-0.5 ml-1 mr-3 text-xs font-extrabold uppercase tracking-wide text-slate-600"
        :class="needAttention.length ? 'mt-3' : 'mt-1'"
      >
        Funcionan bien · {{ allGood.length }}
      </h2>
      <ul class="flex flex-col">
        <li v-for="client in allGood" :key="client.organizationId">
          <button
            type="button"
            class="flex min-h-10 items-center gap-2.5 px-3 py-1.5 text-left text-slate-700"
            :class="rowClass(client)"
            :aria-current="client.organizationId === selectedId ? 'true' : undefined"
            @click="$emit('select', client.organizationId)"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="shrink-0 text-success-dark" aria-hidden="true">
              <path d="m5 12 5 5 9-10" />
            </svg>
            <span
              class="min-w-0 flex-1 truncate text-sm"
              :class="client.organizationId === selectedId ? 'font-bold text-aqua-800' : ''"
            >
              {{ client.organizationName }}
            </span>
            <span class="whitespace-nowrap text-xs text-slate-600">
              <template v-if="client.counts.sensors">
                {{ client.counts.working }} de {{ client.counts.sensors - client.counts.neverSent }} funcionan
              </template>
              <template v-else>sin sensores</template>
            </span>
          </button>
        </li>
      </ul>
    </template>
  </nav>
</template>

<script setup>
import { computed } from "vue";
import { formatDuration, minutesSince } from "../../utils/alertText";
import { clientIssue } from "../../utils/sensorMaintenance";

const props = defineProps({
  // sensorTree(sites, sensors, "problems")
  tree: { type: Array, default: () => [] },
  selectedId: { type: String, default: null },
  // Changes on every refresh, so "hace X" is recomputed
  now: { type: Date, default: () => new Date() },
});

defineEmits(["select"]);

const needAttention = computed(() => props.tree.filter((c) => c.problems > 0));
const allGood = computed(() =>
  props.tree
    .filter((c) => !c.problems)
    .sort((a, b) => a.organizationName.localeCompare(b.organizationName, "es")),
);

// The chosen one is white and reaches the right edge (it joins its card);
// the others keep a gap on the right
function rowClass(client) {
  return client.organizationId === props.selectedId
    ? "w-full rounded-l-lg bg-white shadow-[inset_4px_0_0_theme(colors.aqua.600)]"
    : "mr-3 w-[calc(100%-0.75rem)] rounded-lg hover:bg-white/70";
}

function issue(client) {
  return clientIssue(client) ?? { kind: "pressure", text: "" };
}

function issueText(client) {
  const found = issue(client);
  if (found.offlineSince) {
    return `sin conexión desde hace ${formatDuration(minutesSince(found.offlineSince, props.now))}`;
  }
  return found.text;
}
</script>
