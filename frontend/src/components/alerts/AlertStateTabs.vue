<!--
  ALERT STATE TABS (#252)
  Underlined tabs with their number in a pill: Sin atender (red when there
  is any) · En curso · Arregladas (last 7 days). The short explanation of
  each tab is its tooltip. Arrows move between tabs (WAI-ARIA tabs).
-->

<template>
  <div class="border-b border-slate-200">
    <div
      role="tablist"
      aria-label="Estado de las alertas"
      class="-mb-px flex gap-x-1 overflow-x-auto sm:gap-x-7"
    >
      <button
        v-for="(tab, index) in tabs"
        :id="`alert-tab-${tab.state}`"
        :key="tab.state"
        ref="buttons"
        type="button"
        role="tab"
        :aria-selected="tab.state === modelValue"
        :tabindex="tab.state === modelValue ? 0 : -1"
        aria-controls="alert-tab-panel"
        :title="tab.hint"
        class="flex flex-1 shrink-0 items-center justify-center gap-1 whitespace-nowrap border-b-[3px] pb-3 pt-2.5 text-[13px] transition sm:flex-none sm:justify-start sm:gap-2 sm:text-[15px]"
        :class="
          tab.state === modelValue
            ? 'border-aqua-600 font-bold text-aqua-900'
            : 'border-transparent font-semibold text-slate-600 hover:text-slate-900'
        "
        @click="$emit('update:modelValue', tab.state)"
        @keydown.right.prevent="move(index, 1)"
        @keydown.left.prevent="move(index, -1)"
      >
        {{ tab.label }}
        <span
          class="min-w-[1.25rem] rounded-full px-1.5 text-center text-xs sm:min-w-[1.4rem] sm:px-2 sm:text-[13px]"
          :class="
            tab.state === 'ACTIVE' && tab.count > 0
              ? 'bg-rose-700 text-white'
              : 'bg-slate-200 text-slate-700'
          "
        >
          {{ tab.count ?? "…" }}
        </span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

const props = defineProps({
  // [{ state, label, hint, count }]
  tabs: { type: Array, required: true },
  modelValue: { type: String, required: true },
});

const emit = defineEmits(["update:modelValue"]);
const buttons = ref([]);

function move(index, step) {
  const next = (index + step + props.tabs.length) % props.tabs.length;
  emit("update:modelValue", props.tabs[next].state);
  buttons.value[next]?.focus();
}
</script>
