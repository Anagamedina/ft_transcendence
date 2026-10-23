<!--
  ALERT CARD (F21)
  One alert as a card, in client language:
    - Severity with icon + text (Urgente / Aviso): never colour alone.
    - What happened (alert type), where (building · floor · sensor) and when
      (local time). Fixed alerts show the date of the fix on top, so the
      date matches the order of the "Arreglado" tab.
    - Who acted: "Se encarga <name>" (ACKNOWLEDGED) or "Detectado <date> ·
      arreglo confirmado por <name>" (RESOLVED).
    - Severity help (tooltip + screen readers): what Urgente / Aviso mean.
    - While the alert is open, the AquaGuard message: we watch it, we contact
      the client if nobody acts, we confirm the fix with the readings.
    - "Me encargo" button only while nobody has acted (state ACTIVE).
  Presentational: it receives the alert by props and emits "acknowledge";
  the parent calls the API. Reused by the building page (F25) and the admin
  alerts (F22).
  Usage:
    <AlertCard :alert="alert" :busy="busyId === alert.id" @acknowledge="ack" />
    <AlertCard :alert="alert" show-state :show-action="false" />
-->

<template>
  <article
    class="flex h-full flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4"
    :aria-labelledby="titleId"
  >
    <!-- Severity + optional state, both with text -->
    <div class="flex flex-wrap items-center gap-2">
      <span
        class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold"
        :class="severity.pill"
        :title="severity.help"
      >
        <span class="h-4 w-4" aria-hidden="true"><AppIcon name="alert" /></span>
        {{ severity.text }}
        <span class="sr-only">: {{ severity.help }}</span>
      </span>
      <span
        v-if="showState"
        class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
        :class="state.pill"
      >
        <span
          class="h-1.5 w-1.5 rounded-full"
          :class="state.dot"
          aria-hidden="true"
        ></span>
        {{ state.text }}
      </span>
      <time
        class="ml-auto whitespace-nowrap text-xs text-slate-600"
        :datetime="headDate"
      >
        {{ formatDateTime(headDate) }}
      </time>
    </div>

    <!-- What and where -->
    <div class="min-w-0">
      <h3 :id="titleId" class="font-semibold text-slate-900">
        {{ typeText }}
      </h3>
      <p class="mt-0.5 text-sm text-slate-700">{{ whereText }}</p>
      <p v-if="alert.sensor_name" class="text-sm text-slate-600">
        Sensor: {{ alert.sensor_name }}
      </p>
    </div>

    <!-- Who acted -->
    <p v-if="actedText" class="text-sm text-slate-700">{{ actedText }}</p>

    <!-- AquaGuard message while the alert is open -->
    <p
      v-if="alert.state !== 'RESOLVED'"
      class="rounded-lg bg-slate-50 p-3 text-sm text-slate-700"
    >
      AquaGuard está vigilando este problema. Si no se atiende, nos pondremos en
      contacto contigo. Cuando esté arreglado, lo confirmaremos con las
      lecturas.
    </p>

    <!-- Single client action -->
    <div v-if="showAction && alert.state === 'ACTIVE'" class="mt-auto pt-1">
      <button
        type="button"
        class="w-full rounded-lg bg-aqua-600 px-4 py-2 text-sm font-semibold text-white hover:bg-aqua-700 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
        :disabled="busy"
        :aria-describedby="titleId"
        @click="$emit('acknowledge', alert.id)"
      >
        {{ busy ? "Guardando…" : "Me encargo" }}
      </button>
    </div>
  </article>
</template>

<script setup>
import { computed } from "vue";
import AppIcon from "./AppIcon.vue";
import { useLabels } from "../composables/useLabels";
import { useFormat } from "../composables/useFormat";
import { floorLabel } from "../utils/floors.js";

const props = defineProps({
  // AlertResponse: type, severity, state, site_name, floor, sensor_name,
  // created_at, acknowledged_at, resolved_at, acknowledged_by_name,
  // resolved_by_name
  alert: { type: Object, required: true },
  // True while "Me encargo" is being saved: disables the button
  busy: { type: Boolean, default: false },
  // Show the state pill (the alerts page already shows it in the tabs)
  showState: { type: Boolean, default: false },
  // Show "Me encargo" (false for read-only places)
  showAction: { type: Boolean, default: true },
});

defineEmits(["acknowledge"]);

const { label, toneClasses } = useLabels();
const { formatDateTime } = useFormat();

// Client words. Same texts as the landing and the admin (shared decision).
// Backend rule (alerts/rules.py): CRITICAL when the reading leaves its range
// by more than 20 % or the sensor goes offline; WARNING otherwise.
const SEVERITY = {
  CRITICAL: {
    text: "Urgente",
    tone: "danger",
    help: "Actúa ya: puede haber una fuga o el sensor no está vigilando.",
  },
  WARNING: {
    text: "Aviso",
    tone: "warning",
    help: "Vigílalo: la presión está un poco fuera de lo normal.",
  },
};
const STATE = {
  ACTIVE: { text: "Pendiente", tone: "danger" },
  ACKNOWLEDGED: { text: "En curso", tone: "info" },
  RESOLVED: { text: "Arreglado", tone: "success" },
};

const severity = computed(() => {
  const item = SEVERITY[props.alert.severity] ?? SEVERITY.WARNING;
  return { text: item.text, help: item.help, ...toneClasses(item.tone) };
});

const state = computed(() => {
  const item = STATE[props.alert.state] ?? { text: "—", tone: "neutral" };
  return { text: item.text, ...toneClasses(item.tone) };
});

const typeText = computed(() => label("AlertType", props.alert.type));

// "Torre Diagonal Mar · Planta 2"
const whereText = computed(() => {
  const parts = [props.alert.site_name];
  if (Number.isInteger(props.alert.floor))
    parts.push(floorLabel(props.alert.floor));
  return parts.filter(Boolean).join(" · ");
});

const actedText = computed(() => {
  const a = props.alert;
  if (a.state === "RESOLVED") {
    const who = a.resolved_by_name ? ` por ${a.resolved_by_name}` : "";
    return `Detectado ${formatDateTime(a.created_at)} · arreglo confirmado${who}`;
  }
  if (a.state === "ACKNOWLEDGED") {
    const who = a.acknowledged_by_name || "Alguien de tu equipo";
    return `Se encarga ${who} · desde ${formatDateTime(a.acknowledged_at)}`;
  }
  return "";
});

// Date on top: when it was fixed (RESOLVED) or when it was detected
const headDate = computed(() =>
  props.alert.state === "RESOLVED" && props.alert.resolved_at
    ? props.alert.resolved_at
    : props.alert.created_at,
);

// Unique id for aria-labelledby
const titleId = computed(() => `alert-${props.alert.id}-title`);
</script>
