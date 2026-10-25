<!--
  ALERT FILTERS (#252)
  One bar: search (client or building; the server also matches the sensor), the chosen client
  as a removable chip (it is chosen from the client cards) and the severity
  as a segmented control on the right (Todas | Críticas | Leves). The search waits 300 ms after the last key.
-->

<template>
  <div class="flex flex-wrap items-center gap-2.5">
    <label
      class="flex h-10 w-full items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 text-slate-500 focus-within:border-aqua-500 focus-within:ring-2 focus-within:ring-aqua-200 sm:w-80"
    >
      <span class="sr-only">Buscar alertas</span>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.5-3.5" />
      </svg>
      <input
        :value="draft"
        type="search"
        placeholder="Buscar cliente o edificio…"
        class="min-w-0 flex-1 bg-transparent text-sm text-slate-900 placeholder:text-slate-500 focus:outline-none"
        @input="onInput($event.target.value)"
      />
    </label>

    <span
      v-if="clientName"
      class="inline-flex h-8 items-center gap-1 rounded-full bg-sky-100 pl-3 pr-1 text-sm font-semibold text-aqua-700"
    >
      {{ clientName }}
      <button
        type="button"
        class="flex h-6 w-6 items-center justify-center rounded-full hover:bg-sky-200"
        :aria-label="`Quitar el filtro de cliente ${clientName}`"
        @click="$emit('update:organizationId', null)"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true">
          <path d="M6 6l12 12M18 6 6 18" />
        </svg>
      </button>
    </span>

    <div role="group" aria-label="Urgencia" class="flex rounded-[10px] bg-slate-200 p-[3px] sm:ml-auto">
      <button
        v-for="option in SEVERITIES"
        :key="option.label"
        type="button"
        :aria-pressed="severity === option.value"
        class="flex h-8 items-center gap-1.5 rounded-[7px] px-3 text-[13px] transition"
        :class="
          severity === option.value
            ? 'bg-white font-bold text-aqua-900 shadow-sm'
            : 'font-semibold text-slate-600 hover:text-slate-900'
        "
        @click="$emit('update:severity', option.value)"
      >
        <span v-if="option.dot" class="h-2 w-2 rounded-full" :class="option.dot" aria-hidden="true"></span>
        {{ option.label }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref, watch } from "vue";

const SEVERITIES = [
  { value: null, label: "Todas" },
  { value: "CRITICAL", label: "Críticas", dot: "bg-rose-700" },
  { value: "WARNING", label: "Leves", dot: "bg-amber-600" },
];

const props = defineProps({
  q: { type: String, default: "" },
  severity: { type: String, default: null },
  // Name of the client chosen in the cards; null = all clients
  clientName: { type: String, default: null },
});

const emit = defineEmits(["update:q", "update:organizationId", "update:severity"]);

// What the user is typing; sent to the parent after a pause
const draft = ref(props.q);
let timer = null;

watch(
  () => props.q,
  (value) => {
    if (value !== draft.value) draft.value = value;
  },
);

function onInput(value) {
  draft.value = value;
  clearTimeout(timer);
  timer = setTimeout(() => emit("update:q", value.trim()), 300);
}

onBeforeUnmount(() => clearTimeout(timer));
</script>
