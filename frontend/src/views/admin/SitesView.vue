<!--
  ADMIN SITES VIEW (#169)
  Buildings of every client, from the API (B2): DataTable with search, client
  and district filters and pagination. "+ Nuevo edificio" and "Editar" open
  SiteForm in a Modal. The building name opens its sensors floor by floor.
  Rendered inside AdminLayout.
-->

<template>
  <AdminLayout>
    <section class="space-y-6">
      <header class="flex flex-wrap items-center justify-between gap-4">
        <h1 class="text-2xl font-bold text-slate-900">Edificios</h1>

        <button
          type="button"
          class="min-h-10 rounded-lg bg-aqua-600 px-4 text-sm font-semibold text-white hover:bg-aqua-700 disabled:opacity-50"
          :disabled="status !== 'success'"
          @click="openCreate"
        >
          + Nuevo edificio
        </button>
      </header>

      <DataTable
        :columns="COLUMNS"
        :rows="sites"
        :search-fields="['name', 'address']"
        search-placeholder="Nombre o dirección…"
        :filters="filters"
        :loading="status === 'loading' || status === 'idle'"
        :error="errorMessage"
        item-name="edificios"
        empty-title="No hay edificios registrados"
        empty-message="Los edificios aparecen aquí al dar de alta un cliente o con «Nuevo edificio»."
        icon="building"
        caption="Edificios"
        @retry="loadSites"
      >
        <template #row="{ row: site }">
          <tr>
            <td class="px-4 py-3">
              <RouterLink
                :to="{ path: '/admin/sensors', query: { site: site.id } }"
                class="font-semibold text-aqua-700 hover:underline"
              >
                {{ site.name }}
              </RouterLink>
              <span v-if="site.address" class="block text-xs text-slate-500">{{
                site.address
              }}</span>
            </td>
            <td class="px-4 py-3 text-slate-600">
              {{ site.organization_name }}
            </td>
            <td class="px-4 py-3 text-slate-600">
              {{ label("District", site.district) }}
            </td>
            <td class="px-4 py-3 text-slate-600">
              {{ label("BuildingType", site.building_type) }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-slate-600">
              {{ floorsText(site) }}
            </td>
            <td class="px-4 py-3 text-right tabular-nums text-slate-600">
              {{ site.sensor_count }}
            </td>
            <td class="px-4 py-3">
              <StatusPill type="SiteStatus" :value="site.status" />
            </td>
            <td class="px-4 py-3 text-right">
              <button
                type="button"
                class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
                :aria-label="`Editar ${site.name}`"
                @click="openEdit(site)"
              >
                Editar
              </button>
            </td>
          </tr>
        </template>
      </DataTable>
    </section>

    <!-- Create / edit window. The same SiteForm as the new client wizard -->
    <Modal
      :show="formOpen"
      :title="editing ? 'Editar edificio' : 'Nuevo edificio'"
      size="lg"
      @close="closeForm"
    >
      <form id="site-form" class="space-y-4" novalidate @submit.prevent="save">
        <!-- Only on create: the API needs to know which client owns the building -->
        <div v-if="!editing" class="flex flex-col gap-1">
          <label for="site-client" class="text-sm font-semibold text-gray-700">
            Cliente <span aria-hidden="true">*</span>
          </label>
          <select
            id="site-client"
            ref="clientSelect"
            v-model="clientId"
            required
            class="w-full rounded-lg border bg-white px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-aqua-600"
            :class="clientError ? 'border-red-600' : 'border-gray-300'"
            :aria-invalid="Boolean(clientError)"
            :aria-describedby="clientError ? 'site-client-error' : undefined"
          >
            <option value="" disabled>Elige un cliente</option>
            <option
              v-for="client in clients"
              :key="client.id"
              :value="client.id"
            >
              {{ client.name }}
            </option>
          </select>
          <p
            v-if="clientError"
            id="site-client-error"
            class="text-sm text-red-700"
          >
            {{ clientError }}
          </p>
        </div>

        <!-- On edit the client cannot change (SiteUpdate has no organization_id) -->
        <p v-else class="text-sm text-slate-600">
          Cliente:
          <span class="font-semibold text-slate-800">{{
            editing.organization_name
          }}</span>
        </p>

        <SiteForm ref="siteForm" v-model="form" :taken-names="takenNames" />

        <p
          v-if="saveError"
          role="alert"
          class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800"
        >
          {{ saveError }}
        </p>
      </form>

      <template #footer>
        <button
          type="button"
          class="min-h-10 rounded-lg border border-slate-300 px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          @click="closeForm"
        >
          Cancelar
        </button>
        <button
          type="submit"
          form="site-form"
          class="min-h-10 rounded-lg bg-aqua-600 px-4 text-sm font-semibold text-white hover:bg-aqua-700 disabled:opacity-50"
          :disabled="saving"
        >
          {{ saving ? "Guardando…" : "Guardar edificio" }}
        </button>
      </template>
    </Modal>
  </AdminLayout>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from "vue";
import AdminLayout from "../../layouts/AdminLayout.vue";
import DataTable from "../../components/DataTable.vue";
import StatusPill from "../../components/StatusPill.vue";
import Modal from "../../components/Modal.vue";
import SiteForm, { emptySite } from "../../components/SiteForm.vue";
import { useSitesStore } from "../../stores/sites.js";
import { useLabels } from "../../composables/useLabels";

const sitesStore = useSitesStore();
const { label } = useLabels();

const COLUMNS = [
  { key: "name", label: "Edificio" },
  { key: "organization_name", label: "Cliente" },
  { key: "district", label: "Distrito" },
  { key: "building_type", label: "Tipo" },
  { key: "floors", label: "Plantas" },
  { key: "sensor_count", label: "Sensores" },
  { key: "status", label: "Estado" },
  { key: "actions", label: "Acciones" },
];

const sites = computed(() => sitesStore.sites);
const status = computed(() => sitesStore.status);

const errorMessage = computed(() =>
  status.value === "error"
    ? sitesStore.error?.message || "No se han podido cargar los edificios."
    : "",
);

// Clients that own at least one building, sorted by name. Every client has one:
// the sign-up always creates the first building (first_site, B1).
const clients = computed(() => {
  const byId = new Map();
  for (const site of sites.value)
    byId.set(site.organization_id, site.organization_name);
  return [...byId]
    .map(([id, name]) => ({ id, name }))
    .sort((a, b) => a.name.localeCompare(b.name, "es"));
});

// Districts present in the loaded buildings. The API adds district after B2 (D10):
// until then no building has one and the district filter is not shown.
const districts = computed(() => [
  ...new Set(sites.value.map((site) => site.district).filter(Boolean)),
]);

const filters = computed(() => {
  const list = [
    {
      key: "organization_id",
      label: "Cliente",
      allLabel: "Todos los clientes",
      options: clients.value.map((client) => ({
        value: client.id,
        label: client.name,
      })),
    },
  ];
  if (districts.value.length > 0) {
    list.push({
      key: "district",
      label: "Distrito",
      allLabel: "Todos los distritos",
      options: districts.value
        .map((value) => ({ value, label: label("District", value) }))
        .sort((a, b) => a.label.localeCompare(b.label, "es")),
    });
  }
  return list;
});

// "4 + 2 sót." as in the mockup; just "4" without basements
function floorsText(site) {
  return site.basements > 0
    ? `${site.floors} + ${site.basements} sót.`
    : String(site.floors);
}

async function loadSites() {
  try {
    await sitesStore.fetchSites();
  } catch {
    // The store exposes the error state to the view
  }
}

// ---------------------------------------------------------------------------
// Create / edit form
// ---------------------------------------------------------------------------
const FORM_FIELDS = ["name", "address", "floors", "basements", "building_type"];

const formOpen = ref(false);
// Building being edited, or null when creating a new one
const editing = ref(null);
const form = ref(emptySite());
const clientId = ref("");
const clientError = ref("");
const saveError = ref("");
const saving = ref(false);

const siteForm = ref(null);
const clientSelect = ref(null);

// Names of the other buildings of the chosen client (the one being edited does not count)
const takenNames = computed(() => {
  const ownerId = editing.value
    ? editing.value.organization_id
    : clientId.value;
  if (!ownerId) return [];
  return sites.value
    .filter(
      (site) =>
        site.organization_id === ownerId && site.id !== editing.value?.id,
    )
    .map((site) => site.name);
});

function openCreate() {
  editing.value = null;
  form.value = emptySite();
  clientId.value = "";
  resetMessages();
  formOpen.value = true;
}

function openEdit(site) {
  editing.value = site;
  // Only the fields SiteForm edits; the API sends null for an empty address
  form.value = {
    name: site.name,
    address: site.address ?? "",
    floors: site.floors,
    basements: site.basements,
    building_type: site.building_type,
  };
  resetMessages();
  formOpen.value = true;
}

function closeForm() {
  if (saving.value) return;
  formOpen.value = false;
}

function resetMessages() {
  clientError.value = "";
  saveError.value = "";
}

// Form values ready for the API: trimmed name, empty address sent as null
function payload() {
  const address = form.value.address.trim();
  return {
    name: form.value.name.trim(),
    address: address === "" ? null : address,
    floors: form.value.floors,
    basements: form.value.basements,
    building_type: form.value.building_type,
  };
}

// PATCH sends only what changed, so it never overwrites a field by accident
function changedFields(original, data) {
  return Object.fromEntries(
    FORM_FIELDS.filter(
      (field) => data[field] !== (original[field] ?? null),
    ).map((field) => [field, data[field]]),
  );
}

async function save() {
  resetMessages();

  if (!editing.value && !clientId.value) {
    clientError.value = "Elige el cliente al que pertenece el edificio.";
  }
  const formValid = siteForm.value.validate();
  if (clientError.value) {
    nextTick(() => clientSelect.value?.focus());
    return;
  }
  if (!formValid) return;

  saving.value = true;
  try {
    if (editing.value) {
      const changes = changedFields(editing.value, payload());
      if (Object.keys(changes).length > 0) {
        await sitesStore.updateSite(editing.value.id, changes);
      }
    } else {
      await sitesStore.createSite({
        ...payload(),
        organization_id: clientId.value,
      });
    }
    saving.value = false;
    closeForm();
  } catch (err) {
    // The API explains the problem in Spanish (repeated name, a sensor left
    // outside the new number of floors...). Show its message as it comes.
    saveError.value = err?.message || "No se ha podido guardar el edificio.";
    saving.value = false;
  }
}

onMounted(loadSites);
</script>
