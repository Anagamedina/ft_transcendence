<!--
  SENSOR TAB CARDS (#283)
  The tabs of the Sensores page as three cards: an icon, the number and one
  sentence that says what is inside ("el más antiguo, hace 10 h"). On the
  phone the three fit in one row: number, label and the short note. They
  work as WAI-ARIA tabs: arrows move between them.
-->

<template>
  <div role="tablist" aria-label="Sensores" class="grid grid-cols-3 gap-2 sm:gap-3">
    <button
      v-for="(tab, index) in tabs"
      :id="`sensor-tab-${tab.key}`"
      :key="tab.key"
      ref="buttons"
      type="button"
      role="tab"
      :aria-selected="tab.key === modelValue"
      :tabindex="tab.key === modelValue ? 0 : -1"
      aria-controls="sensor-tab-panel"
      class="flex flex-col items-start gap-0.5 rounded-xl bg-white px-3 py-2.5 text-left transition sm:grid sm:grid-cols-[2.75rem_1fr] sm:items-center sm:gap-x-3 sm:px-4 sm:py-3"
      :class="tab.key === modelValue ? 'border-2 border-aqua-600' : 'border border-slate-200 hover:border-aqua-400'"
      @click="$emit('update:modelValue', tab.key)"
      @keydown.right.prevent="move(index, 1)"
      @keydown.left.prevent="move(index, -1)"
    >
      <span
        class="row-span-2 hidden h-11 w-11 items-center justify-center rounded-lg sm:flex"
        :class="ICON_BOX[tab.key]"
        aria-hidden="true"
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <template v-if="tab.key === 'offline'">
            <path d="M2 8.8a15 15 0 0 1 20 0M5 12.5a10 10 0 0 1 14 0M8.5 16.4a5 5 0 0 1 7 0" />
            <path d="m3 3 18 18" />
          </template>
          <template v-else-if="tab.key === 'floors'">
            <path d="M4 20V8l8-5 8 5v12" />
            <path d="M9 20v-6h6v6" />
          </template>
          <path v-else d="M12 3s7 7.5 7 12a7 7 0 0 1-14 0c0-4.5 7-12 7-12z" />
        </svg>
      </span>
      <span class="text-xs leading-tight text-slate-900 sm:text-[15px]">
        <b class="block text-[22px] leading-none sm:inline">{{ tab.count ?? "…" }}</b> {{ tab.label }}
      </span>
      <span class="hidden text-[13px] sm:block" :class="tab.noteClass || 'text-slate-500'">{{ tab.note }}</span>
      <span v-if="tab.shortNote" class="text-[11px] sm:hidden" :class="tab.noteClass || 'text-slate-500'">{{ tab.shortNote }}</span>
    </button>
  </div>
</template>

<script setup>
import { ref } from "vue";

const props = defineProps({
  // [{ key: 'offline' | 'floors' | 'all', label, count, note, shortNote, noteClass }]
  tabs: { type: Array, required: true },
  modelValue: { type: String, required: true },
});

const emit = defineEmits(["update:modelValue"]);
const buttons = ref([]);

const ICON_BOX = {
  offline: "bg-slate-100 text-slate-600",
  floors: "bg-amber-50 text-amber-700",
  all: "bg-success-light text-success-dark",
};

function move(index, step) {
  const next = (index + step + props.tabs.length) % props.tabs.length;
  emit("update:modelValue", props.tabs[next].key);
  buttons.value[next]?.focus();
}
</script>
