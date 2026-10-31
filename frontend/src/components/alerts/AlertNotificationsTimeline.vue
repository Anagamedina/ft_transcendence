<!--
  ALERT NOTIFICATIONS TIMELINE (#275)
  "Avisos al cliente" in the alert panel: a vertical line with each step.
  Done steps get a ✓ and a solid line; the next one is highlighted with how
  long is left; the rest are grey with a dashed line. When the readings are
  normal again (#277) the last step is green: "Normal desde las 10:32 · se
  cerrará sola a las 10:47". The steps come from
  utils/notificationSteps.js and move on by themselves on each refresh.
-->

<template>
  <section v-if="steps.length" aria-labelledby="alert-notices-title" class="flex flex-col gap-2">
    <h3 id="alert-notices-title" class="text-xs font-bold uppercase tracking-wide text-slate-500">
      Avisos al cliente
    </h3>
    <ol class="flex flex-col text-sm">
      <li
        v-for="(step, index) in steps"
        :key="step.key"
        class="grid grid-cols-[1.25rem_1fr] gap-x-3"
      >
        <span class="flex flex-col items-center" aria-hidden="true">
          <span
            v-if="step.status === 'done'"
            class="mt-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-aqua-600 text-white"
          >
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4">
              <path d="m5 12 5 5 9-10" />
            </svg>
          </span>
          <span
            v-else
            class="mt-1 rounded-full"
            :class="DOT[step.status]"
          ></span>
          <span
            v-if="index < steps.length - 1"
            class="w-0.5 flex-1"
            :class="isSolid(index) ? 'bg-aqua-600' : 'border-l-2 border-dashed border-slate-300'"
          ></span>
        </span>
        <span class="flex flex-col" :class="index < steps.length - 1 ? 'pb-3.5' : ''">
          <span :class="TITLE[step.status]">{{ step.title }}</span>
          <span class="text-xs text-slate-500">{{ step.detail }}</span>
          <span class="sr-only">{{ STATUS_TEXT[step.status] }}</span>
        </span>
      </li>
    </ol>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { notificationSteps } from "../../utils/notificationSteps";

const props = defineProps({
  alert: { type: Object, required: true },
  // Changes on every refresh, so "en 9 min" counts down
  now: { type: Date, default: () => new Date() },
});

const DOT = {
  start: "h-3 w-3 bg-slate-400",
  next: "h-4 w-4 border-[3px] border-aqua-600 bg-white",
  pending: "h-3 w-3 border-2 border-slate-300 bg-white",
  call: "h-4 w-4 bg-danger",
  normal: "h-4 w-4 border-[3px] border-success-dark bg-success-light",
};

const TITLE = {
  start: "font-semibold text-slate-900",
  done: "font-semibold text-slate-900",
  next: "font-semibold text-aqua-600",
  pending: "text-slate-600",
  call: "font-bold text-danger-dark",
  normal: "font-semibold text-success-dark",
};

const STATUS_TEXT = {
  done: "(hecho)",
  next: "(siguiente)",
  pending: "(pendiente)",
  call: "(urgente)",
  normal: "(confirmando que está arreglada)",
};

const steps = computed(() => notificationSteps(props.alert, props.now));

// Solid from the start up to the last done step; dashed after it
function isSolid(index) {
  const next = steps.value[index + 1];
  return next?.status === "done";
}
</script>
