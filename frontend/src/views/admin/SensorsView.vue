<!--
  ADMIN SENSORS VIEW (#283, before #169)
  AquaGuard installs and looks after the sensors (they come with the plan),
  so this page is about the device, not the water (that is Alertas). It
  answers "what do we have to do in the buildings?" with three tabs:

    Sin conexión        sensors to go and check
    Plantas sin sensor  floors where a sensor has to be installed
    Sensores            clients on the left (SensorClientList), the chosen
                        client with all its buildings and floors on the
                        right (SensorClientDetail), joined in one box

  Clicking a sensor opens SensorSidePanel (chart, data, "Ajustar umbrales");
  "+ Añadir sensor" (in a building), "+ Instalar aquí" and "+ Dar de alta"
  (on a floor) open it to create one: always in a chosen building. "Importar CSV"
  creates every sensor of a building from a file (SensorImportDialog). Tab, search, client and building of the
  tab "Sensores" (?client=), building filter (?site=) and open sensor (?sensor=) live
  in the URL. The sensors and buildings come from stores/sensors.js and
  stores/sites.js; refreshed every 30 s (REFRESH_MS).
-->

<template>
  <AdminLayout>
    <section class="flex flex-col gap-5">
      <header class="flex flex-wrap items-center justify-between gap-3">
        <h1 class="text-2xl font-bold text-slate-900">Sensores</h1>
        <button
          type="button"
          class="min-h-10 rounded-lg border border-aqua-600 px-4 text-sm font-semibold text-aqua-700 hover:bg-aqua-50"
          @click="importing = true"
        >
          Importar CSV
        </button>
      </header>

      <div class="flex flex-col gap-3">
        <SensorTabCards :tabs="tabs" :model-value="tab" @update:model-value="setTab" />

        <div class="flex flex-wrap items-center gap-2.5">
          <label
            class="flex h-10 w-full items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 text-slate-500 focus-within:border-aqua-500 focus-within:ring-2 focus-within:ring-aqua-200 sm:w-80"
          >
            <span class="sr-only">Buscar cliente o edificio</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-3.5-3.5" />
            </svg>
            <input
              :value="draft"
              type="search"
              placeholder="Buscar cliente o edificio…"
              class="min-w-0 flex-1 bg-transparent text-sm text-slate-900 placeholder:text-slate-500 focus:outline-none"
              @input="onSearch($event.target.value)"
            />
          </label>
          <span
            v-if="siteFilter"
            class="inline-flex h-8 items-center gap-1 rounded-full bg-aqua-100 pl-3 pr-1 text-sm font-semibold text-aqua-700"
          >
            {{ siteFilter.name }}
            <button
              type="button"
              class="flex h-6 w-6 items-center justify-center rounded-full hover:bg-aqua-200"
              :aria-label="`Quitar el filtro de edificio ${siteFilter.name}`"
              @click="updateQuery({ site: null })"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true">
                <path d="M6 6l12 12M18 6 6 18" />
              </svg>
            </button>
          </span>
        </div>
      </div>

      <div id="sensor-tab-panel" role="tabpanel" :aria-labelledby="`sensor-tab-${tab}`">
        <LoadingState v-if="loading" message="Cargando sensores…" />
        <ErrorState
          v-else-if="loadError"
          :message="apiErrorMessage(loadError, 'No se han podido cargar los sensores.')"
          @retry="refresh"
        />

        <template v-else-if="tab === 'floors'">
          <p
            v-if="!missingFloors.length"
            class="rounded-xl border border-success/40 bg-success-light p-8 text-center font-semibold text-success-dark"
          >
            ✓ Todas las plantas tienen sensor
          </p>
          <template v-else>
            <MissingFloorsList :rows="missingFloors" @install="openCreate" />
            <p class="mt-3 text-[13px] text-slate-500">
              El plan incluye un sensor por planta: estas plantas todavía no lo tienen.
            </p>
          </template>
        </template>

        <OfflineByBuilding
          v-else-if="tab === 'offline'"
          :stopped="offline.stopped"
          :contacts="extra.contacts"
          :selected-id="selected?.id ?? null"
          :now="now"
          @open="openSensor"
        />

        <template v-else>
          <p
            v-if="!tree.length"
            class="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-600"
          >
            {{ q || siteFilter ? "Ningún cliente o edificio coincide con la búsqueda." : "Todavía no hay edificios." }}
          </p>
          <!-- One box: the clients on grey, the chosen one joined to its card.
               On the phone, the list or the client; side by side from lg -->
          <div v-else class="overflow-hidden rounded-2xl border border-slate-200 bg-white lg:grid lg:grid-cols-[22rem_minmax(0,1fr)]">
            <div class="bg-slate-100" :class="filters.client ? 'hidden lg:block' : ''">
              <SensorClientList
                class="lg:sticky lg:top-0"
                :tree="tree"
                :selected-id="selectedClient?.organizationId ?? null"
                :now="now"
                @select="selectClient"
              />
            </div>
            <SensorClientDetail
              v-if="selectedClient"
              class="p-4 sm:p-5"
              :class="filters.client ? '' : 'hidden lg:flex'"
              :client="selectedClient"
              :selected-sensor-id="selected?.id ?? null"
              :alert-counts="extra.alertCounts"
              :contact="extra.contacts[selectedClient.organizationId] ?? null"
              :now="now"
              @back="updateQuery({ client: null })"
              @open="openSensor"
              @install="openCreate"
            />
          </div>
        </template>
      </div>
    </section>

    <SensorSidePanel
      :open="panel.open"
      :mode="panel.mode"
      :sensor="selected"
      :sites="sitesStore.sites"
      :sensors="sensorsStore.sensors"
      :preset="panel.preset"
      :alert-count="selected ? extra.alertCounts[selected.id] ?? 0 : 0"
      :contact="selected ? extra.contacts[selected.organization_id] : null"
      :busy="saving"
      :error="saveError"
      @close="closePanel"
      @edit="panel.mode = 'edit'"
      @cancel="panel.mode = 'detail'"
      @save="save"
    />

    <SensorImportDialog
      :show="importing"
      :sites="sitesStore.sites"
      @close="importing = false"
      @imported="refresh"
    />
  </AdminLayout>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import AdminLayout from "../../layouts/AdminLayout.vue";
import LoadingState from "../../components/LoadingState.vue";
import ErrorState from "../../components/ErrorState.vue";
import SensorTabCards from "../../components/sensors/SensorTabCards.vue";
import OfflineByBuilding from "../../components/sensors/OfflineByBuilding.vue";
import SensorClientList from "../../components/sensors/SensorClientList.vue";
import SensorClientDetail from "../../components/sensors/SensorClientDetail.vue";
import MissingFloorsList from "../../components/sensors/MissingFloorsList.vue";
import SensorSidePanel from "../../components/sensors/SensorSidePanel.vue";
import SensorImportDialog from "../../components/sensors/SensorImportDialog.vue";
import { useSitesStore } from "../../stores/sites.js";
import { useSensorsStore } from "../../stores/sensors.js";
import { useAdminSensorsStore } from "../../stores/adminSensors.js";
import { useListQuery } from "../../composables/useListQuery";
import { REFRESH_MS, useAutoRefresh } from "../../composables/useAutoRefresh";
import { apiErrorMessage } from "../../utils/apiError";
import { floorsWithoutSensor, isOffline, sensorTree, splitOffline } from "../../utils/sensorMaintenance";
import { formatDuration, minutesSince } from "../../utils/alertText";

const PAGE_SIZE = 20;
const TABS = ["offline", "floors", "all"];

const sitesStore = useSitesStore();
const sensorsStore = useSensorsStore();
const extra = useAdminSensorsStore();
const { q, filters, page, updateQuery, setSearch } = useListQuery({ pageSize: PAGE_SIZE });

// URL → what the page shows
const tab = computed(() => (TABS.includes(filters.value.tab) ? filters.value.tab : "offline"));
const siteFilter = computed(() =>
  filters.value.site ? sitesStore.siteById(filters.value.site) ?? null : null,
);

// --- Search (waits 300 ms after the last key) ---
const draft = ref(q.value);
let timer = null;
watch(q, (value) => {
  if (value !== draft.value) draft.value = value;
});
function onSearch(value) {
  draft.value = value;
  clearTimeout(timer);
  timer = setTimeout(() => setSearch(value.trim()), 300);
}

function matches(text) {
  return text?.toLowerCase().includes(q.value.toLowerCase());
}

// Sensors after the building filter and the search
const filtered = computed(() =>
  sensorsStore.sensors.filter(
    (s) =>
      (!siteFilter.value || s.site_id === siteFilter.value.id) &&
      (!q.value ||
        [s.site_name, s.organization_name].some(matches)),
  ),
);

// Stopped sending (a failure) and never sent (installation not finished)
const offline = computed(() => splitOffline(filtered.value));

// Tab "Sensores": the buildings that match (by their name or their client),
// each with all its floors, grouped by client
const tree = computed(() => {
  const sites = sitesStore.sites.filter(
    (s) =>
      (!siteFilter.value || s.id === siteFilter.value.id) &&
      (!q.value || [s.name, s.organization_name].some(matches)),
  );
  return sensorTree(sites, sensorsStore.sensors, "problems");
});

// The client (?client=) shown on the right, with all its buildings. On a
// computer, without a choice: the first client with problems
const selectedClient = computed(
  () => tree.value.find((c) => c.organizationId === filters.value.client) ?? tree.value[0] ?? null,
);

function selectClient(id) {
  updateQuery({ client: id });
}

const missingFloors = computed(() => {
  const sites = sitesStore.sites.filter(
    (s) =>
      (!siteFilter.value || s.id === siteFilter.value.id) &&
      (!q.value || [s.name, s.organization_name].some(matches)),
  );
  return floorsWithoutSensor(sites, sensorsStore.sensors);
});

const tabs = computed(() => {
  const stopped = offline.value.stopped;
  const oldest = stopped.length
    ? Math.max(...stopped.map((s) => minutesSince(s.last_seen_at, now.value) ?? 0))
    : null;
  const working = filtered.value.filter((s) => !isOffline(s)).length;
  return [
    {
      key: "offline",
      label: "sin conexión",
      count: stopped.length,
      note: stopped.length ? `el más antiguo, hace ${formatDuration(oldest)}` : "todos envían lecturas",
      shortNote: stopped.length ? `hace ${formatDuration(oldest)}` : "",
      noteClass: stopped.length ? "font-semibold text-warning-dark" : "font-semibold text-success-dark",
    },
    {
      key: "floors",
      label: "plantas sin sensor",
      count: missingFloors.value.reduce((n, row) => n + row.missing.length, 0),
      note: `en ${missingFloors.value.length} ${missingFloors.value.length === 1 ? "edificio" : "edificios"}`,
    },
    {
      key: "all",
      label: "sensores",
      count: filtered.value.length,
      note: `${working} funcionan`,
      shortNote: `${working} funcionan`,
      noteClass: "font-semibold text-success-dark",
    },
  ];
});

function setTab(value) {
  updateQuery({ tab: value === "offline" ? null : value, page: 1 });
}

// --- Data ---
const loading = computed(
  () => !sensorsStore.sensors.length && ["idle", "loading"].includes(sensorsStore.status),
);
const loadError = computed(() =>
  sensorsStore.status === "error" ? sensorsStore.error : sitesStore.status === "error" ? sitesStore.error : null,
);

const now = ref(new Date());

async function refresh() {
  now.value = new Date();
  await Promise.allSettled([
    sensorsStore.fetchSensors(),
    sitesStore.fetchSites(),
    extra.fetchAlertCounts(),
    extra.fetchContacts(),
  ]);
}

onMounted(refresh);

// "Importar CSV": the dialog reloads the list through refresh when it creates sensors
const importing = ref(false);
// Every REFRESH_MS, everything: a new building or a changed contact shows up
// without reloading the page
useAutoRefresh(refresh, REFRESH_MS);
onBeforeUnmount(() => clearTimeout(timer));

// --- Side panel. The open sensor lives in the URL (?sensor=), so
//     "Ver sensor" from Alertas opens it directly ---
const panel = reactive({ open: false, mode: "detail", preset: null });
const selected = computed(
  () => sensorsStore.sensors.find((s) => s.id === filters.value.sensor) ?? null,
);

watch(
  selected,
  (sensor) => {
    if (sensor && !panel.open) {
      panel.mode = "detail";
      panel.open = true;
    }
  },
  { immediate: true },
);

function openSensor(sensor) {
  saveError.value = "";
  panel.mode = "detail";
  panel.open = true;
  updateQuery({ sensor: sensor.id, page: page.value });
}

function openCreate(preset = null) {
  saveError.value = "";
  updateQuery({ sensor: null, page: page.value });
  panel.preset = preset ? { siteId: preset.site.id, floor: preset.floor } : null;
  panel.mode = "create";
  panel.open = true;
}

function closePanel() {
  panel.open = false;
  updateQuery({ sensor: null, page: page.value });
}

// --- Create / edit (the API explains the problem: repeated label, floor
//     outside the building, thresholds…) ---
const saving = ref(false);
const saveError = ref("");
const EDITABLE = ["name", "floor", "min_pressure", "max_pressure"];

async function save({ mode, siteId, data }) {
  saving.value = true;
  saveError.value = "";
  try {
    if (mode === "create") {
      const created = await sensorsStore.createSensor({
        site_id: siteId,
        external_id: data.external_id.trim(),
        name: data.name.trim(),
        floor: data.floor,
        min_pressure: data.min_pressure,
        max_pressure: data.max_pressure,
      });
      panel.mode = "detail";
      updateQuery({ sensor: created.id, page: page.value });
    } else {
      const current = selected.value;
      const values = { ...data, name: data.name.trim() };
      const changes = Object.fromEntries(
        EDITABLE.filter((f) => values[f] !== current[f]).map((f) => [f, values[f]]),
      );
      if (Object.keys(changes).length) await sensorsStore.updateSensor(current.id, changes);
      panel.mode = "detail";
    }
  } catch (err) {
    saveError.value = apiErrorMessage(err, "No se ha podido guardar el sensor.");
  } finally {
    saving.value = false;
  }
}
</script>
