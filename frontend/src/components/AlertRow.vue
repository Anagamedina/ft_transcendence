<!--
  ALERT ROW
  One row of an alerts table (<tr>): message, client (optional), sensor, severity, state
  (with when it was acknowledged or resolved), date (with how long it has been
  open or how long it lasted) and the acknowledge / resolve buttons.
  Presentational: it receives the alert by props and emits the chosen action;
  the parent calls the store.
  Client views pass :show-organization="false" (no client column).
  Usage (inside <tbody>):
    <AlertRow
      v-for="alert in alerts" :key="alert.id"
      :alert="alert"
      :busy="busyAlertId === alert.id"
      @acknowledge="acknowledge"
      @resolve="resolve"
    />
-->

<template>
  <tr>
    <td class="min-w-48 px-4 py-3 text-slate-800">
      {{ alert.message || "—" }}
      <span class="block text-xs text-slate-500">{{
        label("AlertType", alert.type)
      }}</span>
    </td>
    <td v-if="showOrganization" class="px-4 py-3 text-slate-600">
      {{ alert.organization_name || "—" }}
    </td>
    <td class="px-4 py-3 text-slate-600">
      {{ alert.sensor_name || "—" }}
      <span class="block text-xs text-slate-500">{{ alert.site_name }}</span>
    </td>
    <td class="px-4 py-3">
      <StatusPill type="AlertSeverity" :value="alert.severity" />
    </td>
    <td class="px-4 py-3">
      <StatusPill type="AlertState" :value="alert.state" />
      <span
        v-if="actionDate"
        class="mt-1 block whitespace-nowrap text-xs text-slate-500"
      >
        {{ actionDate }}
      </span>
    </td>
    <td class="whitespace-nowrap px-4 py-3 text-slate-600">
      {{ formatDateTime(alert.created_at) }}
      <span v-if="durationText" class="block text-xs text-slate-500">{{
        durationText
      }}</span>
    </td>
    <td class="whitespace-nowrap px-4 py-3">
      <div class="flex flex-wrap gap-2">
        <!-- Acknowledge: only while nobody has seen it yet (state ACTIVE) -->
        <button
          v-if="alert.state === 'ACTIVE'"
          type="button"
          class="rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-medium hover:bg-slate-50 disabled:opacity-50"
          :disabled="busy"
          @click="$emit('acknowledge', alert.id)"
        >
          Reconocer
        </button>
        <!-- Resolve: while the stored status is ACTIVE, acknowledged or not -->
        <button
          v-if="alert.status === 'ACTIVE'"
          type="button"
          class="rounded-md bg-aqua-900 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-aqua-800 disabled:opacity-50"
          :disabled="busy"
          @click="$emit('resolve', alert.id)"
        >
          Resolver
        </button>
        <span v-if="alert.status === 'RESOLVED'" class="text-xs text-slate-500">
          Sin acciones
        </span>
      </div>
    </td>
  </tr>
</template>

<script setup>
import { computed } from "vue";
import StatusPill from "./StatusPill.vue";
import { useLabels } from "../composables/useLabels";
import { useFormat } from "../composables/useFormat";

const props = defineProps({
  // AlertResponse: message, type, organization_name, sensor_name, site_name,
  // severity, status (ACTIVE | RESOLVED), state (ACTIVE | ACKNOWLEDGED | RESOLVED),
  // created_at, acknowledged_at, resolved_at
  alert: { type: Object, required: true },
  // True while an action on this alert is running: disables its buttons
  busy: { type: Boolean, default: false },
  // Client column: the admin needs it, a client only sees its own organization
  showOrganization: { type: Boolean, default: true },
});

// Both events send the alert id
defineEmits(["acknowledge", "resolve"]);

const { label } = useLabels();
// Dates in local time: 'hoy 08:20', 'ayer 17:05', '8 sept 10:20'
const { parseDate: toDate, formatDateTime } = useFormat();

// Human duration: "menos de 1 min", "25 min", "3 h 10 min", "2 d 4 h"
function formatDuration(ms) {
  const minutes = Math.floor(ms / 60000);
  if (minutes < 1) return "menos de 1 min";
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24)
    return minutes % 60 ? `${hours} h ${minutes % 60} min` : `${hours} h`;
  const days = Math.floor(hours / 24);
  return hours % 24 ? `${days} d ${hours % 24} h` : `${days} d`;
}

// When the last action happened: shown under the state pill
const actionDate = computed(() => {
  const {
    state,
    acknowledged_at: acknowledgedAt,
    resolved_at: resolvedAt,
  } = props.alert;
  if (state === "RESOLVED" && toDate(resolvedAt))
    return formatDateTime(resolvedAt);
  if (state === "ACKNOWLEDGED" && toDate(acknowledgedAt))
    return formatDateTime(acknowledgedAt);
  return "";
});

// How long it has been open (still active) or how long it lasted (resolved)
const durationText = computed(() => {
  const start = toDate(props.alert.created_at);
  if (!start) return "";
  const resolved = toDate(props.alert.resolved_at);
  const end = resolved || new Date();
  if (end < start) return "";
  const text = formatDuration(end - start);
  return resolved ? `Duró ${text}` : `Abierta ${text}`;
});
</script>
