<!--
  TABS
  Accessible tabs (WAI-ARIA tabs pattern): only the active tab is in the Tab
  order, Left/Right move between tabs (wrapping around), Home/End go to the
  first/last one. Each tab's content goes in a named slot with the tab key.
  Usage:
    <Tabs v-model="activeTab" :tabs="TABS" label="Secciones del cliente">
      <template #sites>...</template>
      <template #users>...</template>
    </Tabs>
-->

<template>
  <div class="space-y-6">
    <div class="overflow-x-auto">
      <div
        role="tablist"
        :aria-label="label"
        class="flex min-w-max gap-1 border-b-2 border-slate-200"
      >
        <button
          v-for="(tab, index) in tabs"
          :id="tabId(tab.key)"
          :key="tab.key"
          :ref="(el) => (buttons[index] = el)"
          type="button"
          role="tab"
          :aria-selected="modelValue === tab.key"
          :aria-controls="panelId(tab.key)"
          :tabindex="modelValue === tab.key ? 0 : -1"
          class="-mb-0.5 border-b-2 px-4 py-2.5 text-base"
          :class="
            modelValue === tab.key
              ? 'border-aqua-600 font-bold text-aqua-600'
              : 'border-transparent text-slate-600 hover:text-aqua-600'
          "
          @click="select(index)"
          @keydown="onKeydown($event, index)"
        >
          {{ tab.label }}
        </button>
      </div>
    </div>

    <!-- Only the active panel is rendered -->
    <div
      :id="panelId(modelValue)"
      role="tabpanel"
      :aria-labelledby="tabId(modelValue)"
      tabindex="0"
    >
      <slot :name="modelValue" />
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from "vue";

const props = defineProps({
  // List of tabs: [{ key: 'sites', label: 'Edificios' }, ...]
  tabs: { type: Array, required: true },
  // Key of the active tab (use with v-model)
  modelValue: { type: String, required: true },
  // Accessible name of the tab list, read by screen readers
  label: { type: String, required: true },
  // Optional prefix for the ids; set it only if one page has two Tabs.
  // Without it the ids are tab-<key> and panel-<key>.
  idPrefix: { type: String, default: "" },
});

const emit = defineEmits(["update:modelValue"]);

const buttons = ref([]);

function tabId(key) {
  return props.idPrefix ? `${props.idPrefix}-tab-${key}` : `tab-${key}`;
}

function panelId(key) {
  return props.idPrefix ? `${props.idPrefix}-panel-${key}` : `panel-${key}`;
}

// Activates a tab and moves the focus to its button
function select(index) {
  emit("update:modelValue", props.tabs[index].key);
  nextTick(() => buttons.value[index]?.focus());
}

// Left/Right go to the previous/next tab (wrapping around), Home/End to the first/last
function onKeydown(event, index) {
  const last = props.tabs.length - 1;
  const moves = {
    ArrowRight: index === last ? 0 : index + 1,
    ArrowLeft: index === 0 ? last : index - 1,
    Home: 0,
    End: last,
  };
  if (!(event.key in moves)) return;
  event.preventDefault();
  select(moves[event.key]);
}
</script>
