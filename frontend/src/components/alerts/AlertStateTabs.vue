<!--
  ALERT STATE TABS (#252)
  Underlined tabs with their number: Sin atender (red pill when there is
  any) · En curso · Arregladas ("N esta semana"). The short explanation of
  each tab is its tooltip. Arrows move between tabs (WAI-ARIA tabs).
-->

<template>
  <div class="border-b border-slate-200">
    <div role="tablist" aria-label="Estado de las alertas" class="flex flex-wrap gap-x-7">
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
        class="-mb-px flex items-center gap-2 border-b-[3px] pb-3 pt-2.5 text-[15px] transition"
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
        <span v-if="tab.state === 'RESOLVED'" class="text-[13px] font-normal text-slate-500">
          {{ tab.count ?? "…" }} esta semana
        </span>
        <span
          v-else
          class="min-w-[1.4rem] rounded-full px-2 text-center text-[13px]"
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
