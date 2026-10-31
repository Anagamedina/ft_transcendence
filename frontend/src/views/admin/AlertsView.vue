<!--
  ADMIN ALERTS VIEW (#252)
  "Primero lo que nadie está atendiendo". From top to bottom: clients with
  open alerts (cards), the three states (Sin atender · En curso ·
  Arregladas), filters and the table. A row opens AlertDetailPanel, where
  AquaGuard marks the alert as fixed.

  Everything comes from the server (stores/adminAlerts.js): counts never stop
  at 100. Tab, filters and page live in the URL, so a reload or a shared link
  shows the same thing. Refreshes every 30 s (REFRESH_MS) while the tab is visible.
-->

<template>
  <AdminLayout>
    <section class="flex flex-col gap-6">
      <header class="flex flex-wrap items-center justify-between gap-3">
        <h1 class="text-2xl font-bold text-slate-900">Alertas</h1>
        <p class="flex items-center gap-1.5 text-sm text-slate-500" aria-live="polite">
          <span
            class="h-2 w-2 rounded-full"
            :class="store.status === 'error' ? 'bg-danger' : 'bg-success'"
            aria-hidden="true"
          ></span>
          {{ updatedText }}
        </p>
      </header>

      <AlertClientCards
        :clients="store.clientsWithAlerts"
        :selected-id="organizationId"
        @select="setFilter('organization_id', $event)"
      />

      <div class="flex flex-col gap-3">
        <AlertStateTabs :tabs="tabs" :model-value="state" @update:model-value="setTab" />

        <AlertFilters
          :q="q"
          :severity="severity"
          :client-name="clientName"
          @update:q="setSearch"
          @update:organization-id="setFilter('organization_id', $event)"
          @update:severity="setFilter('severity', $event)"
        />
      </div>

      <div
        id="alert-tab-panel"
        role="tabpanel"
        :aria-labelledby="`alert-tab-${state}`"
        :aria-busy="store.status === 'loading' || store.status === 'refreshing'"
      >
        <LoadingState v-if="store.status === 'loading' || store.status === 'idle'" />

        <ErrorState
          v-else-if="store.status === 'error'"
          :message="apiErrorMessage(store.error, 'No se han podido cargar las alertas.')"
          @retry="refresh"
        />

        <div
          v-else-if="allClear"
          class="flex flex-col items-center gap-1 rounded-xl border border-success/40 bg-success-light p-10 text-center"
        >
          <p class="text-xl font-bold text-success-dark">✓ Todo en orden</p>
          <p class="text-sm text-success-dark">
            No hay ninguna alerta abierta. Las arregladas de la semana están en «Arregladas».
          </p>
        </div>

        <p
          v-else-if="!store.rows.length"
          class="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-600"
        >
          {{ emptyText }}
        </p>

        <template v-else>
          <p
            v-if="store.truncated"
            class="mb-3 rounded-lg bg-warning-light p-3 text-sm text-warning-dark"
          >
            Hay más de 100 alertas en esta pestaña: se ordenan las 100 más recientes.
            Filtra por cliente o urgencia para ver el resto.
          </p>
          <AdminAlertsTable
            :rows="store.rows"
            :state="state"
            :page="page"
            :page-size="pageSize"
            :total="store.total"
            :selected-id="selected?.id ?? null"
            :client-filtered="Boolean(organizationId)"
            :now="now"
            @open="open"
            @page="setPage"
          />
        </template>
      </div>
    </section>

    <AlertDetailPanel
      :alert="selected"
      :busy="resolving"
      :error="resolveError"
      :now="now"
      @close="selected = null"
      @resolve="resolve"
    />
  </AdminLayout>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import AdminLayout from "../../layouts/AdminLayout.vue";
import LoadingState from "../../components/LoadingState.vue";
import ErrorState from "../../components/ErrorState.vue";
import AlertClientCards from "../../components/alerts/AlertClientCards.vue";
import AlertStateTabs from "../../components/alerts/AlertStateTabs.vue";
import AlertFilters from "../../components/alerts/AlertFilters.vue";
import AdminAlertsTable from "../../components/alerts/AdminAlertsTable.vue";
import AlertDetailPanel from "../../components/alerts/AlertDetailPanel.vue";
import { useAdminAlertsStore } from "../../stores/adminAlerts";
import { useOverviewStore } from "../../stores/overview";
import { useListQuery } from "../../composables/useListQuery";
import { REFRESH_MS, useAutoRefresh } from "../../composables/useAutoRefresh";
import { useLabels } from "../../composables/useLabels";
import { apiErrorMessage } from "../../utils/apiError";

const STATES = ["ACTIVE", "ACKNOWLEDGED", "RESOLVED"];
const HINTS = {
  ACTIVE: "Nadie se ha encargado aún",
  ACKNOWLEDGED: "El cliente dice que se encarga",
  RESOLVED: "Detectadas en los últimos 7 días",
};

const store = useAdminAlertsStore();
const overviewStore = useOverviewStore();
const { label } = useLabels();
const { q, filters, page, pageSize, updateQuery, setSearch, setFilter, setPage } =
  useListQuery({ pageSize: 20 });

// URL → what the page shows
const state = computed(() =>
  STATES.includes(filters.value.state) ? filters.value.state : "ACTIVE",
);
const organizationId = computed(() => filters.value.organization_id ?? null);
const severity = computed(() => filters.value.severity ?? null);
const hasFilters = computed(() => Boolean(q.value || organizationId.value || severity.value));

const query = computed(() => ({
  state: state.value,
  organization_id: organizationId.value,
  severity: severity.value,
  q: q.value,
  page: page.value,
  pageSize: pageSize.value,
}));

const tabs = computed(() =>
  STATES.map((value) => ({
    state: value,
    label: value === "RESOLVED" ? "Arregladas" : label("AlertState", value),
    hint: HINTS[value],
    count: store.counts[value],
  })),
);

// Chip of the client chosen in the cards (also when it came in the URL)
const clientName = computed(() =>
  organizationId.value
    ? store.organizations.find((o) => o.id === organizationId.value)?.name ?? "Cliente"
    : null,
);

const allClear = computed(
  () =>
    !hasFilters.value &&
    state.value !== "RESOLVED" &&
    store.counts.ACTIVE === 0 &&
    store.counts.ACKNOWLEDGED === 0,
);

const emptyText = computed(() => {
  if (hasFilters.value) return "Ninguna alerta coincide con estos filtros.";
  if (state.value === "ACTIVE") return "Todas las alertas abiertas tienen a alguien encargándose.";
  if (state.value === "ACKNOWLEDGED") return "Ningún cliente se está encargando de una alerta ahora mismo.";
  return "Ninguna alerta detectada en los últimos 7 días está arreglada.";
});

// "Actualizado hace 20 s": `now` ticks every 10 s
const now = ref(new Date());
const ticker = setInterval(() => (now.value = new Date()), 10000);
onBeforeUnmount(() => clearInterval(ticker));

const updatedText = computed(() => {
  if (!store.updatedAt) return "Cargando…";
  const seconds = Math.max(0, Math.round((now.value - store.updatedAt) / 1000));
  if (seconds < 60) return `Actualizado hace ${seconds} s`;
  return `Actualizado hace ${Math.round(seconds / 60)} min`;
});

// DATA
function loadList() {
  return store.fetchList(query.value);
}

function loadCounts() {
  return store.fetchCounts({
    organization_id: organizationId.value,
    severity: severity.value,
    q: q.value,
  });
}

async function refresh() {
  now.value = new Date();
  await Promise.all([loadList(), loadCounts(), store.fetchOrganizations()]);
}

// Any change in the URL reloads the list. Open tabs page in memory, so
// changing page there needs no request.
watch(
  () => [state.value, organizationId.value, severity.value, q.value],
  () => {
    loadList();
    loadCounts();
  },
);
watch(page, () => {
  if (state.value === "RESOLVED") loadList();
  else store.pageOpen(page.value, pageSize.value);
});

onMounted(refresh);
useAutoRefresh(refresh, REFRESH_MS);

// FILTERS
function setTab(value) {
  selected.value = null;
  updateQuery({ state: value === "ACTIVE" ? null : value, page: 1 });
}

// DETAIL PANEL
const selected = ref(null);
const resolving = ref(false);
const resolveError = ref("");

// On each refresh the open panel takes the new data of its alert, so the
// notices timeline moves on (#275)
watch(
  () => store.rows,
  (rows) => {
    if (!selected.value) return;
    const fresh = rows.find((row) => row.id === selected.value.id);
    if (fresh) selected.value = fresh;
  },
);

function open(alert) {
  resolveError.value = "";
  selected.value = alert;
}

async function resolve(id) {
  resolving.value = true;
  resolveError.value = "";
  try {
    await store.resolve(id);
    selected.value = null;
    await refresh();
    overviewStore.fetchOverview().catch(() => {});
  } catch (err) {
    resolveError.value = apiErrorMessage(err, "No se ha podido cerrar la alerta.");
  } finally {
    resolving.value = false;
  }
}
</script>
