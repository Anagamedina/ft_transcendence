<!--
  CLIENTS LIST
  Presentational table of client organizations for the admin zone:
  status, trial, counters, expandable buildings and sensors, and pagination.
  Receives data via props only and emits events; the parent decides what to do.
-->

<template>
  <section class="space-y-4">
    <div
      class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
    >
      <h2 class="text-lg font-bold text-gray-800">Clientes</h2>

      <!-- Search box: visual only. Filtering logic belongs to the parent view -->
      <label class="w-full sm:w-72">
        <span class="sr-only">Buscar cliente</span>
        <input
          type="search"
          :value="search"
          placeholder="Buscar cliente…"
          class="input input-bordered w-full"
          @input="$emit('update:search', $event.target.value)"
        />
      </label>
    </div>

    <LoadingState v-if="loading" message="Cargando clientes…" />

    <ErrorState v-else-if="error" :message="error" @retry="$emit('retry')" />

    <!-- Two empty cases: no clients at all, or none matching the current filter/search -->
    <EmptyState
      v-else-if="clients.length === 0"
      :title="filtered ? 'Ningún cliente coincide' : 'No hay clientes todavía'"
      :message="
        filtered
          ? 'Prueba con otro estado u otra búsqueda.'
          : 'Cuando des de alta un cliente aparecerá aquí.'
      "
      icon="building"
    />

    <!-- overflow-x-auto: on narrow screens the table scrolls inside its card, not the whole page -->
    <div
      v-else
      class="overflow-x-auto rounded-xl border border-gray-200 bg-white"
    >
      <table class="w-full min-w-[760px] text-sm">
        <caption class="sr-only">
          Clientes
        </caption>
        <thead class="bg-gray-50 text-left text-gray-600">
          <tr>
            <!-- sticky left-0: the client name stays visible while the table scrolls sideways -->
            <th
              scope="col"
              class="sticky left-0 bg-gray-50 px-4 py-3 font-semibold"
            >
              Cliente
            </th>
            <th scope="col" class="px-4 py-3 font-semibold">Estado</th>
            <th scope="col" class="px-4 py-3 font-semibold">Prueba</th>
            <th scope="col" class="px-4 py-3 font-semibold text-right">
              Edificios
            </th>
            <th scope="col" class="px-4 py-3 font-semibold text-right">
              Sensores
            </th>
            <th scope="col" class="px-4 py-3 font-semibold text-right">
              Usuarios
            </th>
            <th scope="col" class="px-4 py-3 font-semibold text-right">
              Alertas
            </th>
          </tr>
        </thead>
        <!-- One tbody per client keeps the expandable row keyed without a template wrapper. -->
        <tbody v-for="{ client, status } in rows" :key="client.id">
          <tr class="border-t border-gray-200">
            <th
              scope="row"
              class="sticky left-0 bg-white px-4 py-3 text-left font-semibold"
            >
              <div class="flex items-center gap-2">
                <!-- Expand button: only when the client has buildings -->
                <button
                  v-if="client.site_count > 0"
                  type="button"
                  class="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-lg text-gray-500 hover:bg-aqua-50 hover:text-aqua-600"
                  :aria-expanded="isExpanded(client.id)"
                  :aria-controls="`sites-${client.id}`"
                  :aria-label="`Edificios de ${client.name}`"
                  @click="toggle(client.id)"
                >
                  <span
                    aria-hidden="true"
                    class="inline-block transition-transform"
                    :class="isExpanded(client.id) ? 'rotate-90' : ''"
                    >›</span
                  >
                </button>
                <!-- Same width as the button, so the names stay aligned -->
                <span v-else class="w-7 shrink-0" aria-hidden="true"></span>

                <!-- Button styled as a link: the parent decides where to navigate -->
                <button
                  type="button"
                  class="text-aqua-600 hover:text-aqua-900 hover:underline text-left"
                  @click="$emit('select', client)"
                >
                  {{ client.name }}
                </button>
              </div>
            </th>
            <td class="px-4 py-3">
              <span
                class="inline-block whitespace-nowrap rounded-full px-3 py-1 text-xs font-semibold"
                :class="status.pillClass"
              >
                {{ status.label }}
              </span>
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-gray-600">
              {{ status.trialText }}
            </td>
            <td class="px-4 py-3 text-right tabular-nums">
              {{ client.site_count }}
            </td>
            <td class="px-4 py-3 text-right tabular-nums">
              {{ client.sensor_count }}
            </td>
            <td class="px-4 py-3 text-right tabular-nums">
              {{ client.user_count }}
            </td>
            <!-- Red when at least one open alert is critical -->
            <td
              class="px-4 py-3 text-right tabular-nums font-bold"
              :class="
                client.critical_alerts > 0 ? 'text-red-700' : 'text-gray-800'
              "
            >
              {{ client.open_alerts }}
            </td>
          </tr>

          <!-- Expanded row: the client's buildings and their sensors -->
          <tr
            v-if="isExpanded(client.id)"
            :id="`sites-${client.id}`"
            class="bg-aqua-50"
          >
            <td colspan="7" class="px-4 py-3">
              <ul class="sticky left-4 w-fit space-y-3 pl-9">
                <li v-for="site in sitesOf(client.id)" :key="site.id">
                  <p class="font-semibold text-gray-800">
                    {{ site.name }}
                    <span class="font-normal text-gray-600"
                      >· {{ sensorsLabel(site.sensors.length) }}</span
                    >
                  </p>
                  <p v-if="site.address" class="text-gray-600">
                    {{ site.address }}
                  </p>
                  <ul
                    v-if="site.sensors.length > 0"
                    class="mt-1 space-y-1 border-l-2 border-aqua-100 pl-3"
                  >
                    <li
                      v-for="sensor in site.sensors"
                      :key="sensor.id"
                      class="text-gray-700"
                    >
                      {{ sensor.name }}
                      <span class="text-gray-500">
                        · {{ sensor.location }} · {{ sensorStateLabel(sensor) }}
                      </span>
                    </li>
                  </ul>
                </li>
              </ul>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination: only when there is something to paginate -->
    <div
      v-if="!loading && !error && total > 0"
      class="flex flex-col gap-3 text-sm text-gray-600 sm:flex-row sm:items-center sm:justify-between"
    >
      <label class="flex items-center gap-2">
        Por página
        <select
          class="select select-bordered select-sm"
          :value="pageSize"
          @change="$emit('update:pageSize', Number($event.target.value))"
        >
          <option v-for="size in pageSizes" :key="size" :value="size">
            {{ size }}
          </option>
        </select>
      </label>

      <!-- aria-live: screen readers announce the new range when the page changes -->
      <p aria-live="polite" class="tabular-nums">
        {{ rangeStart }}–{{ rangeEnd }} de {{ total }}
      </p>

      <nav aria-label="Paginación" class="flex flex-wrap gap-1">
        <button
          type="button"
          :class="pageButtonClass(false)"
          :disabled="page <= 1"
          @click="$emit('update:page', page - 1)"
        >
          Anterior
        </button>
        <button
          v-for="number in pages"
          :key="number"
          type="button"
          :class="pageButtonClass(number === page)"
          :aria-current="number === page ? 'page' : undefined"
          @click="$emit('update:page', number)"
        >
          {{ number }}
        </button>
        <button
          type="button"
          :class="pageButtonClass(false)"
          :disabled="page >= pages"
          @click="$emit('update:page', page + 1)"
        >
          Siguiente
        </button>
      </nav>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from "vue";
import LoadingState from "./LoadingState.vue";
import ErrorState from "./ErrorState.vue";
import EmptyState from "./EmptyState.vue";
import { useClientStatus } from "../composables/useClientStatus";
import { useLabels } from "../composables/useLabels";

const props = defineProps({
  // Each client follows OrganizationResponse:
  // { id, name, status, trial_ends_at, site_count, sensor_count, user_count, open_alerts, critical_alerts, ... }
  clients: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: "" },
  // Current search text (use with v-model:search in the parent)
  search: { type: String, default: "" },
  // True when a filter or search is active: changes the empty-state message
  filtered: { type: Boolean, default: false },
  // Returns the buildings of a client, each with its sensors: (clientId) => [{ ..., sensors: [] }]
  sitesOf: { type: Function, default: () => [] },
  // Pagination. total = clients matching the filter in every page, not only this one
  total: { type: Number, default: 0 },
  // Current page, starting at 1 (use with v-model:page in the parent)
  page: { type: Number, default: 1 },
  // Clients per page (use with v-model:pageSize in the parent)
  pageSize: { type: Number, default: 10 },
  pageSizes: { type: Array, default: () => [10, 25] },
});

defineEmits([
  "select",
  "retry",
  "update:search",
  "update:page",
  "update:pageSize",
]);

// Pairs each client with its translated status, computed once per client
// instead of calling useClientStatus several times inside the template
const rows = computed(() =>
  props.clients.map((client) => ({ client, status: useClientStatus(client) })),
);

// Which clients are expanded, by id. Pure UI state, so it lives here
const expanded = ref({});

function isExpanded(clientId) {
  return Boolean(expanded.value[clientId]);
}

function toggle(clientId) {
  expanded.value[clientId] = !expanded.value[clientId];
}

function sensorsLabel(count) {
  return count === 1 ? "1 sensor" : `${count} sensores`;
}

const { label } = useLabels();

// Sensor state in Spanish, from useLabels. Accepts the B3 `health` values
// and the older `status` ones (ONLINE means it sends readings: OK).
function sensorStateLabel(sensor) {
  const state = sensor.health ?? sensor.status;
  if (!state) return "Desconocido";
  return label("SensorHealth", state === "ONLINE" ? "OK" : state);
}

// Number of pages: rounded up (8 clients, 3 per page → 3 pages)
const pages = computed(() => Math.ceil(props.total / props.pageSize));

// Range shown in "1–10 de 23"
const rangeStart = computed(() => (props.page - 1) * props.pageSize + 1);
const rangeEnd = computed(() =>
  Math.min(props.page * props.pageSize, props.total),
);

// Same look as the status filter buttons; the current page is filled in aqua
function pageButtonClass(isCurrent) {
  const base =
    "min-h-9 min-w-9 rounded-lg border px-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50";
  return isCurrent
    ? `${base} border-aqua-600 bg-aqua-600 text-white`
    : `${base} border-gray-300 bg-white text-gray-700 hover:border-aqua-600`;
}
</script>
