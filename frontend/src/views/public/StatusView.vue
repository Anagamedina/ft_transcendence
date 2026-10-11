<template>
  <PublicLayout>
    <div class="max-w-3xl w-full mx-auto px-6 py-12">
      <h1 class="text-2xl font-bold text-aqua-900 mb-2">Estado del servicio</h1>

      <LoadingState v-if="!report" message="Comprobando el estado…" />

      <template v-else>
        <p class="text-sm text-gray-500 mb-8">
          Última comprobación: {{ formatDate(report.checked_at) }}
        </p>

        <div
          class="rounded-xl border px-6 py-4 mb-8 font-semibold"
          :class="STATES[report.status].banner"
        >
          {{ SUMMARIES[report.status] }}
        </div>

        <ul class="space-y-3">
          <li
            v-for="component in report.components"
            :key="component.name"
            class="flex items-center justify-between gap-4 rounded-xl border border-gray-200 bg-white px-6 py-4"
          >
            <div>
              <p class="font-semibold text-gray-900">{{ NAMES[component.name] }}</p>
              <p class="text-sm text-gray-500">{{ describe(component) }}</p>
            </div>
            <span
              class="shrink-0 rounded-full px-3 py-1 text-sm font-semibold"
              :class="STATES[component.status].badge"
            >
              {{ STATES[component.status].label }}
            </span>
          </li>
        </ul>

        <button
          type="button"
          class="mt-8 min-h-[44px] px-5 rounded-lg border border-aqua-700 text-aqua-700 font-semibold hover:bg-aqua-50 transition disabled:opacity-50"
          :disabled="loading"
          @click="load"
        >
          {{ loading ? "Comprobando…" : "Comprobar de nuevo" }}
        </button>
      </template>
    </div>
  </PublicLayout>
</template>

<script setup>
import { onMounted, ref } from "vue";
import PublicLayout from "../../layouts/PublicLayout.vue";
import LoadingState from "../../components/LoadingState.vue";
import statusService from "../../services/status.service.js";

const STATES = {
  OPERATIONAL: {
    label: "Operativo",
    badge: "bg-green-100 text-green-800",
    banner: "border-green-200 bg-green-50 text-green-800",
  },
  DEGRADED: {
    label: "Degradado",
    badge: "bg-yellow-100 text-yellow-800",
    banner: "border-yellow-200 bg-yellow-50 text-yellow-800",
  },
  DOWN: {
    label: "Caído",
    badge: "bg-red-100 text-red-800",
    banner: "border-red-200 bg-red-50 text-red-800",
  },
};

const SUMMARIES = {
  OPERATIONAL: "Todos los sistemas funcionan con normalidad.",
  DEGRADED: "El servicio funciona, pero algún componente necesita atención.",
  DOWN: "El servicio no está disponible.",
};

const NAMES = {
  backend: "API",
  database: "Base de datos",
  simulator: "Simulador de sensores",
  backup: "Copias de seguridad",
};

const report = ref(null);
const loading = ref(false);

function formatDate(value) {
  return new Date(value).toLocaleString("es-ES");
}

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function describe(component) {
  if (component.name === "simulator") {
    return component.last_event_at
      ? `Último dato recibido: ${formatDate(component.last_event_at)}`
      : "Todavía no se ha recibido ningún dato";
  }
  if (component.name === "backup") {
    return component.last_event_at
      ? `Última copia: ${formatDate(component.last_event_at)} (${formatSize(component.size_bytes)})`
      : "Todavía no hay ninguna copia";
  }
  return component.status === "OPERATIONAL" ? "Responde con normalidad" : "No responde";
}

// If the request itself fails, the API is the component that is down.
async function load() {
  loading.value = true;
  try {
    const response = await statusService.getStatus();
    report.value = response.data;
  } catch {
    report.value = {
      status: "DOWN",
      checked_at: new Date().toISOString(),
      components: [{ name: "backend", status: "DOWN" }],
    };
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>
