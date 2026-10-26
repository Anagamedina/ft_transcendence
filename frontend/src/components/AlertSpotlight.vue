<!--
  ALERT SPOTLIGHT (F25)
  The most important open alert of a building, big, at the top of its page:
    - Drop icon and the problem in words ("Presión demasiado baja"), where
      (sensor · floor) and since when.
    - What it may mean, in client words, by alert type.
    - Sin atender: "Me encargo". En curso: who is handling it.
    - "Ver gráfico": the parent opens "Plantas y sensores" on that floor.
    - One AquaGuard line (we watch it and close it after checking readings).
  Pending is red, en curso blue; both also say it in text.
  Usage:
    <AlertSpotlight :alert="alert" :busy="busy" @acknowledge="ack"
                    @chart="openFloor" />
-->

<template>
  <section
    class="flex flex-wrap items-center gap-5 rounded-2xl border bg-white px-6 py-5"
    :class="pending ? toneClasses('danger').border : toneClasses('info').border"
    aria-labelledby="spotlight-title"
  >
    <!-- Drop with an exclamation mark -->
    <svg width="52" height="52" viewBox="0 0 64 64" aria-hidden="true">
      <path
        d="M32 6 C32 6 14 28 14 39 a18 18 0 0 0 36 0 C50 28 32 6 32 6 Z"
        :fill="pending ? status.danger.DEFAULT : status.info.DEFAULT"
      />
      <rect x="29.5" y="26" width="5" height="15" rx="2.5" fill="#fff" />
      <circle cx="32" cy="47" r="3" fill="#fff" />
    </svg>

    <div class="min-w-0 flex-[1_1_280px] space-y-1">
      <p
        class="text-sm font-semibold"
        :class="pending ? 'text-danger-dark' : 'text-info-dark'"
      >
        {{ pending ? label("AlertState", "ACTIVE") : label("AlertState", "ACKNOWLEDGED") }} ·
        {{ label("AlertSeverity", alert.severity) }}
      </p>
      <h2
        id="spotlight-title"
        class="text-xl font-bold"
        :class="pending ? 'text-danger-dark' : 'text-info-dark'"
      >
        {{ problemText }}
      </h2>
      <p class="text-sm text-slate-700">
        {{ whereText }} · detectado {{ formatRelative(alert.created_at) }}.
        {{ adviceText }}
      </p>
      <p v-if="!pending" class="text-sm text-slate-700">
        Se encarga
        {{ alert.acknowledged_by_name || "alguien de tu equipo" }} desde
        {{ formatDateTime(alert.acknowledged_at) }}.
      </p>
      <p class="text-sm text-slate-600">
        AquaGuard lo sigue vigilando y, cuando esté arreglado, revisará las
        lecturas para cerrarlo.
      </p>
    </div>

    <div class="flex flex-wrap items-center gap-3">
      <button
        type="button"
        class="text-sm font-medium text-aqua-700 underline hover:text-aqua-900"
        @click="$emit('chart', alert.floor)"
      >
        Ver gráfico
      </button>
      <button
        v-if="pending"
        type="button"
        class="rounded-lg bg-aqua-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-aqua-700 disabled:cursor-not-allowed disabled:opacity-60"
        :disabled="busy"
        @click="$emit('acknowledge', alert.id)"
      >
        {{ busy ? "Guardando…" : "Me encargo" }}
      </button>
    </div>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { status } from "../theme/palette.js";
import { useLabels } from "../composables/useLabels";
import { useFormat } from "../composables/useFormat";
import { floorLabel } from "../utils/floors.js";

const props = defineProps({
  // AlertResponse (state ACTIVE or ACKNOWLEDGED)
  alert: { type: Object, required: true },
  busy: { type: Boolean, default: false },
});

defineEmits(["acknowledge", "chart"]);

const { label, toneClasses } = useLabels();
const { formatRelative, formatDateTime } = useFormat();

// The problem and what it may mean, in client words
const PROBLEMS = {
  HIGH_PRESSURE: {
    text: "Presión demasiado alta",
    advice: "Puede dañar la instalación: conviene avisar a tu fontanero.",
  },
  LOW_PRESSURE: {
    text: "Presión demasiado baja",
    advice: "Puede indicar una fuga: conviene avisar a tu fontanero.",
  },
  SENSOR_OFFLINE: {
    text: "Sensor sin conexión",
    advice: "Mientras no envíe datos, esa zona no está vigilada.",
  },
};

const pending = computed(() => props.alert.state === "ACTIVE");
const problem = computed(
  () =>
    PROBLEMS[props.alert.type] ?? { text: "Problema detectado", advice: "" },
);
const problemText = computed(() => problem.value.text);
const adviceText = computed(() => problem.value.advice);

// "Presión planta 6 · Planta 6"
const whereText = computed(() =>
  [
    props.alert.sensor_name,
    Number.isInteger(props.alert.floor) ? floorLabel(props.alert.floor) : null,
  ]
    .filter(Boolean)
    .join(" · "),
);
</script>
