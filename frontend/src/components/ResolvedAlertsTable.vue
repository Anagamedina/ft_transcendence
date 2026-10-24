<!--
  RESOLVED ALERTS TABLE (F21)
  History of fixed alerts, compact and easy to scan:
    Gravedad · Problema · Dónde · Detectado · Arreglado · Confirmado por
  From 1024 px: a real <table> with every column, "Confirmado por" included.
  Below 1024 px (phones and tablets, where the sidebar leaves no room for six
  columns): one compact row per alert, with who confirmed it, so there is
  never horizontal scroll.
  Presentational: it only receives the alerts already filtered and sorted.
  Reused by the building page (F25, "Tu semana").
  Usage:
    <ResolvedAlertsTable :alerts="alerts" caption="Avisos arreglados" />
-->

<template>
  <div class="rounded-xl border border-slate-200 bg-white">
    <!-- Desktop (1024 px and up, where the table fits beside the sidebar) -->
    <table class="hidden w-full text-sm lg:table">
      <caption class="sr-only">
        {{
          caption
        }}
      </caption>
      <thead
        class="border-b border-slate-200 bg-slate-50 text-left text-xs font-semibold uppercase text-slate-600"
      >
        <tr>
          <th scope="col" class="px-4 py-3">Gravedad</th>
          <th scope="col" class="px-4 py-3">Problema</th>
          <th scope="col" class="px-4 py-3">Dónde</th>
          <th scope="col" class="px-4 py-3">Detectado</th>
          <th scope="col" class="px-4 py-3">Arreglado</th>
          <th scope="col" class="px-4 py-3">Confirmado por</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-100">
        <tr v-for="alert in alerts" :key="alert.id" class="hover:bg-slate-50">
          <td class="whitespace-nowrap px-4 py-3">
            <SeverityTag :severity="alert.severity" />
          </td>
          <td class="px-4 py-3 font-medium text-slate-900">
            {{ label("AlertType", alert.type) }}
          </td>
          <td class="px-4 py-3 text-slate-700">
            {{ whereText(alert) }}
            <span
              v-if="alert.sensor_name"
              class="block text-xs text-slate-600"
              >{{ alert.sensor_name }}</span
            >
          </td>
          <td class="whitespace-nowrap px-4 py-3 text-slate-700">
            {{ formatDateTime(alert.created_at) }}
          </td>
          <td class="whitespace-nowrap px-4 py-3 text-slate-700">
            {{ formatDateTime(alert.resolved_at) }}
            <span
              v-if="alert.resolution_minutes != null"
              class="block text-xs text-slate-600"
              >en {{ durationText(alert.resolution_minutes) }}</span
            >
          </td>
          <td class="px-4 py-3 text-slate-700">
            {{ confirmedBy(alert) }}
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Phones and tablets: one compact row per alert -->
    <ul class="divide-y divide-slate-100 lg:hidden" :aria-label="caption">
      <li v-for="alert in alerts" :key="alert.id" class="space-y-1 p-3">
        <div class="flex items-center justify-between gap-2">
          <SeverityTag :severity="alert.severity" />
          <span class="text-xs text-slate-600">
            Arreglado {{ formatDateTime(alert.resolved_at) }}
          </span>
        </div>
        <p class="font-medium text-slate-900">
          {{ label("AlertType", alert.type) }}
        </p>
        <p class="text-sm text-slate-700">
          {{ whereText(alert)
          }}<template v-if="alert.sensor_name">
            · {{ alert.sensor_name }}</template
          >
        </p>
        <p class="text-xs text-slate-600">
          Detectado {{ formatDateTime(alert.created_at) }} · confirmado por
          {{ confirmedBy(alert) }}
        </p>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { h } from "vue";
import AppIcon from "./AppIcon.vue";
import { useLabels } from "../composables/useLabels";
import { useFormat } from "../composables/useFormat";
import { floorLabel } from "../utils/floors.js";

defineProps({
  // AlertResponse list, already filtered and sorted by the parent
  alerts: { type: Array, required: true },
  // Accessible name of the table / list
  caption: { type: String, default: "Avisos arreglados" },
});

const { label, toneClasses } = useLabels();
const { formatDateTime } = useFormat();

// Same words as AlertCard: icon + text, never colour alone
const SEVERITY = {
  CRITICAL: { text: "Urgente", tone: "danger" },
  WARNING: { text: "Aviso", tone: "warning" },
};

// Small severity pill, defined here to keep the table in one file
const SeverityTag = (props) => {
  const item = SEVERITY[props.severity] ?? SEVERITY.WARNING;
  return h(
    "span",
    {
      class: `inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${toneClasses(item.tone).pill}`,
    },
    [
      h("span", { class: "h-3.5 w-3.5", "aria-hidden": "true" }, [
        h(AppIcon, { name: "alert" }),
      ]),
      item.text,
    ],
  );
};
SeverityTag.props = ["severity"];

// Who closed it; AquaGuard when the name is not stored
function confirmedBy(alert) {
  return alert.resolved_by_name || "AquaGuard";
}

// "Hotel Gòtic Centro · Planta 6"
function whereText(alert) {
  const parts = [alert.site_name];
  if (Number.isInteger(alert.floor)) parts.push(floorLabel(alert.floor));
  return parts.filter(Boolean).join(" · ");
}

// resolution_minutes -> "25 min", "3 h 10 min", "2 d 4 h"
function durationText(value) {
  const minutes = Math.round(value);
  if (minutes < 60) return `${Math.max(minutes, 1)} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24)
    return minutes % 60 ? `${hours} h ${minutes % 60} min` : `${hours} h`;
  const days = Math.floor(hours / 24);
  return hours % 24 ? `${days} d ${hours % 24} h` : `${days} d`;
}
</script>
