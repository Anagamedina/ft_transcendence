<!--
  ADMIN ALERTS VIEW
  All alerts with counters, a "Pendientes" block with every open alert
  (F22), the sensors with most alerts and a DataTable (search, client /
  state / severity filters, pagination). Each row is an AlertRow; this view
  calls the store when a row asks to acknowledge or resolve.
-->

<template>
  <AdminLayout>
    <section class="space-y-6">
      <header class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-slate-900">Alertas</h1>
          <p class="mt-1 text-sm text-slate-600">
            Consulta y gestiona las alertas de los sensores.
          </p>
        </div>

        <button
          type="button"
          class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium hover:bg-slate-50"
          :disabled="status === 'loading'"
          @click="loadAlerts"
        >
          Actualizar
        </button>
      </header>

      <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div class="rounded-xl border border-slate-200 bg-white p-4">
          <p class="text-sm text-slate-500">Sin reconocer</p>
          <p class="mt-1 text-2xl font-semibold">{{ pendingCount }}</p>
        </div>
        <div class="rounded-xl border border-slate-200 bg-white p-4">
          <p class="text-sm text-slate-500">Reconocidas</p>
          <p class="mt-1 text-2xl font-semibold">{{ acknowledgedCount }}</p>
        </div>
        <div class="rounded-xl border border-slate-200 bg-white p-4">
          <p class="text-sm text-slate-500">Críticas abiertas</p>
          <p class="mt-1 text-2xl font-semibold">{{ criticalCount }}</p>
        </div>
        <div class="rounded-xl border border-slate-200 bg-white p-4">
          <p class="text-sm text-slate-500">Resueltas</p>
          <p class="mt-1 text-2xl font-semibold">{{ resolvedCount }}</p>
        </div>
      </div>

      <!-- F22: open alerts first, without touching the table filters -->
      <section
        class="rounded-xl border border-slate-200 bg-white"
        aria-labelledby="pending-title"
      >
        <div class="flex items-center justify-between gap-3 p-4">
          <h2 id="pending-title" class="text-sm font-semibold text-slate-800">
            Pendientes
          </h2>
          <span
            v-if="pendingAlerts.length > 0"
            class="text-sm text-slate-500"
          >
            {{ pendingAlerts.length }} abiertas
          </span>
        </div>

        <p v-if="pendingStatus === 'loading'" class="px-4 pb-4 text-sm text-slate-500">
          Cargando alertas pendientes...
        </p>
        <p
          v-else-if="pendingStatus === 'error'"
          class="px-4 pb-4 text-sm text-red-700"
          role="alert"
        >
          No se pudieron cargar las alertas pendientes.
        </p>
        <p
          v-else-if="pendingAlerts.length === 0"
          class="px-4 pb-4 text-sm text-slate-500"
        >
          Sin alertas pendientes.
        </p>

        <div v-else class="overflow-x-auto border-t border-slate-200">
          <table class="min-w-full divide-y divide-slate-200 text-left text-sm">
            <caption class="sr-only">Alertas pendientes</caption>
            <thead class="bg-slate-50 text-slate-600">
              <tr>
                <th
                  v-for="column in COLUMNS"
                  :key="column.key"
                  scope="col"
                  class="px-4 py-3 font-medium"
                >
                  {{ column.label }}
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <AlertRow
                v-for="alert in pendingAlerts"
                :key="alert.id"
                :alert="alert"
                :busy="busyAlertId === alert.id"
                @acknowledge="acknowledge"
                @resolve="resolve"
              />
            </tbody>
          </table>
        </div>
      </section>

      <div
        v-if="sensorRanking.length > 0"
        class="rounded-xl border border-slate-200 bg-white p-4"
      >
        <h2 class="text-sm font-semibold text-slate-800">
          Sensores con más alertas
        </h2>
        <ol class="mt-3 divide-y divide-slate-100 text-sm">
          <li
            v-for="(sensor, index) in sensorRanking"
            :key="sensor.id"
            class="flex items-center gap-3 py-2"
          >
            <span class="w-5 text-slate-500">{{ index + 1 }}</span>
            <span class="min-w-0 flex-1 truncate text-slate-800">
              {{ sensor.name }}
              <span class="text-slate-500">· {{ sensor.site }}</span>
            </span>
            <span class="font-semibold text-slate-900">{{ sensor.total }}</span>
          </li>
        </ol>
      </div>

      <div
        v-if="actionError"
        class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        role="alert"
      >
        {{ actionError }}
      </div>

      <DataTable
        :columns="COLUMNS"
        :rows="alerts"
        :search-fields="[
          'message',
          'type',
          'sensor_name',
          'site_name',
          'organization_name',
        ]"
        search-placeholder="Buscar por mensaje, sensor o cliente..."
        :filters="filters"
        :loading="status === 'loading' || status === 'idle'"
        :error="errorMessage"
        item-name="alertas"
        empty-title="No hay alertas registradas"
        empty-message="Cuando haya alertas disponibles, aparecerán aquí."
        icon="alert"
        caption="Alertas"
        @retry="loadAlerts"
      >
        <template #row="{ row: alert }">
          <AlertRow
            :alert="alert"
            :busy="busyAlertId === alert.id"
            @acknowledge="acknowledge"
            @resolve="resolve"
          />
        </template>
      </DataTable>
    </section>
  </AdminLayout>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import AdminLayout from "../../layouts/AdminLayout.vue";
import DataTable from "../../components/DataTable.vue";
import AlertRow from "../../components/AlertRow.vue";
import { useAlertsStore } from "../../stores/alerts.js";
import alertsService from "../../services/alerts.service.js";
import { useLabels } from "../../composables/useLabels";

const alertStore = useAlertsStore();
const { label } = useLabels();

const COLUMNS = [
  { key: "message", label: "Alerta" },
  { key: "organization_name", label: "Cliente" },
  { key: "sensor_name", label: "Sensor" },
  { key: "severity", label: "Gravedad" },
  { key: "state", label: "Estado" },
  { key: "created_at", label: "Fecha" },
  { key: "actions", label: "Acciones" },
];

// Critical before warning; inside each group, newest first
const SEVERITY_ORDER = { CRITICAL: 0, WARNING: 1 };

const busyAlertId = ref(null);

// F22: own request (status=ACTIVE = not acknowledged + acknowledged), kept
// out of the store so it never overwrites the main table list
const openAlerts = ref([]);
const pendingStatus = ref("idle");
const actionError = ref("");

const alerts = computed(() => alertStore.alerts);
const status = computed(() => alertStore.status);
const error = computed(() => alertStore.error);

const errorMessage = computed(() =>
  status.value === "error"
    ? error.value?.message || "Se ha producido un error inesperado."
    : "",
);

const pendingCount = computed(
  () => alerts.value.filter((alert) => alert.state === "ACTIVE").length,
);

const acknowledgedCount = computed(
  () => alerts.value.filter((alert) => alert.state === "ACKNOWLEDGED").length,
);

const resolvedCount = computed(
  () => alerts.value.filter((alert) => alert.state === "RESOLVED").length,
);

const criticalCount = computed(
  () =>
    alerts.value.filter(
      (alert) => alert.severity === "CRITICAL" && alert.status === "ACTIVE",
    ).length,
);

const pendingAlerts = computed(() =>
  [...openAlerts.value].sort(
    (a, b) =>
      (SEVERITY_ORDER[a.severity] ?? 9) - (SEVERITY_ORDER[b.severity] ?? 9) ||
      new Date(b.created_at) - new Date(a.created_at),
  ),
);

// One option per client that has alerts, sorted by name
const clientOptions = computed(() => {
  const names = new Map();

  for (const alert of alerts.value) {
    names.set(alert.organization_id, alert.organization_name);
  }

  return [...names]
    .map(([value, name]) => ({ value, label: name }))
    .sort((a, b) => a.label.localeCompare(b.label));
});

// Builds the options of an enum filter with the texts from useLabels
function enumOptions(enumName, values) {
  return values.map((value) => ({ value, label: label(enumName, value) }));
}

const filters = computed(() => [
  {
    key: "organization_id",
    label: "Cliente",
    allLabel: "Todos los clientes",
    options: clientOptions.value,
  },
  {
    key: "state",
    label: "Estado",
    allLabel: "Todos los estados",
    options: enumOptions("AlertState", ["ACTIVE", "ACKNOWLEDGED", "RESOLVED"]),
  },
  {
    key: "severity",
    label: "Gravedad",
    allLabel: "Todas las gravedades",
    options: enumOptions("AlertSeverity", ["CRITICAL", "WARNING"]),
  },
]);

const sensorRanking = computed(() => {
  const sensors = new Map();

  for (const alert of alerts.value) {
    const sensor = sensors.get(alert.sensor_id) || {
      id: alert.sensor_id,
      name: alert.sensor_name,
      site: alert.site_name,
      total: 0,
    };

    sensor.total += 1;
    sensors.set(alert.sensor_id, sensor);
  }

  return [...sensors.values()].sort((a, b) => b.total - a.total).slice(0, 5);
});

async function loadPending() {
  pendingStatus.value = "loading";

  try {
    const response = await alertsService.getAlerts({ status: "ACTIVE" });
    openAlerts.value = response.data.items;
    pendingStatus.value = "success";
  } catch {
    openAlerts.value = [];
    pendingStatus.value = "error";
  }
}

// Keeps the pending block in sync after an action from either list:
// resolved alerts leave the block, acknowledged ones are replaced
function syncPending(updated) {
  if (!updated) return;

  if (updated.status === "RESOLVED") {
    openAlerts.value = openAlerts.value.filter((a) => a.id !== updated.id);
    return;
  }

  openAlerts.value = openAlerts.value.map((a) =>
    a.id === updated.id ? updated : a,
  );
}

async function loadAlerts() {
  loadPending();

  try {
    await alertStore.fetchAlerts();
  } catch {
    // The store exposes the error state to the view.
  }
}

async function acknowledge(id) {
  busyAlertId.value = id;
  actionError.value = "";

  try {
    syncPending(await alertStore.acknowledgeAlert(id));
  } catch (err) {
    actionError.value = err?.message || "No se pudo reconocer la alerta.";
  } finally {
    busyAlertId.value = null;
  }
}

async function resolve(id) {
  busyAlertId.value = id;
  actionError.value = "";

  try {
    syncPending(await alertStore.resolveAlert(id));
  } catch (err) {
    actionError.value = err?.message || "No se pudo resolver la alerta.";
  } finally {
    busyAlertId.value = null;
  }
}

onMounted(() => {
  loadAlerts();
});
</script>
