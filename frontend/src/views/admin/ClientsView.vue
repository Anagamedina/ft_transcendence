<!--
  ADMIN CLIENTS VIEW
  Lists client organizations from the API (B1) with a status filter, search, pagination and
  expandable buildings; "+ Nuevo cliente" opens the sign-up wizard on the same page.
  Rendered inside AdminLayout. Data: organizations, sites and sensors stores.
  No district column: OrganizationResponse does not return a district yet.
-->

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '../../layouts/AdminLayout.vue'
import ClientsList from '../../components/ClientsList.vue'
import NewClientWizard from '../../components/NewClientWizard.vue'
import { useOrganizationsStore } from '../../stores/organizations'
import { useSitesStore } from '../../stores/sites'
import { useSensorsStore } from '../../stores/sensors'

const router = useRouter()
const organizationsStore = useOrganizationsStore()
const sitesStore = useSitesStore()
const sensorsStore = useSensorsStore()

// Filter buttons. value matches OrganizationResponse.status; null means "all"
const statusOptions = [
  { value: null, label: 'Todos', countKey: 'all' },
  { value: 'TRIAL', label: 'En prueba', countKey: 'TRIAL' },
  { value: 'ACTIVE', label: 'Activos', countKey: 'ACTIVE' },
  { value: 'SUSPENDED', label: 'Suspendidos', countKey: 'SUSPENDED' },
]

// Page sizes offered to the admin (the API accepts up to 100)
const PAGE_SIZES = [10, 25]

// Wait this long after the last key before searching, so typing a word sends one request
const SEARCH_DELAY_MS = 300

// Everything the admin can change in the list. These four values are exactly
// the query params of GET /api/organizations: status, q, page and page_size
const selectedStatus = ref(null)
const search = ref('')
const page = ref(1)
const pageSize = ref(PAGE_SIZES[0])

// Search text actually sent to the API (updated after SEARCH_DELAY_MS)
const query = ref('')
let searchTimer = null

watch(search, (text) => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => (query.value = text), SEARCH_DELAY_MS)
})

onBeforeUnmount(() => clearTimeout(searchTimer))

// Asks the API for the current page with the current filters
function loadClients() {
  return organizationsStore
    .fetchOrganizations({
      status: selectedStatus.value,
      q: query.value,
      page: page.value,
      page_size: pageSize.value,
    })
    .catch(() => {
      // The store keeps the error; ClientsList shows it with a retry button
    })
}

// A new filter, search or page size changes the results: go back to page 1,
// otherwise the admin could stay on a page that no longer exists.
// If the page was already 1, the page watcher does not fire, so load here
watch([selectedStatus, query, pageSize], () => {
  if (page.value === 1) loadClients()
  else page.value = 1
})

watch(page, loadClients)

// The spinner only on the first load; later the current rows stay until the new ones arrive
const loadedOnce = ref(false)
watch(
  () => organizationsStore.status,
  (value) => {
    if (value === 'success' || value === 'error') loadedOnce.value = true
  }
)
const loading = computed(() => organizationsStore.status === 'loading' && !loadedOnce.value)
const errorMessage = computed(() =>
  organizationsStore.status === 'error'
    ? organizationsStore.error?.message || 'No se han podido cargar los clientes.'
    : ''
)

// True when something hides clients, so the empty state can say "no matches"
const isFiltered = computed(() => selectedStatus.value !== null || query.value.trim() !== '')

// Buildings of a client with their sensors, for the expandable rows.
// Sites and sensors are loaded once for every client; if they fail, rows expand empty
function sitesOf(clientId) {
  return sitesStore.sites
    .filter((site) => site.organization_id === clientId)
    .map((site) => ({
      ...site,
      sensors: sensorsStore.sensors.filter((sensor) => sensor.site_id === site.id),
    }))
}

onMounted(() => {
  loadClients()
  organizationsStore.fetchCounts()
  sitesStore.fetchSites().catch(() => {})
  sensorsStore.fetchSensors().catch(() => {})
})

function openClient(client) {
  router.push(`/admin/clients/${client.id}`)
}

// ---------------------------------------------------------------------------
// New client wizard. Shown instead of the list, on the same route
// ---------------------------------------------------------------------------
const creating = ref(false)
const saving = ref(false)
// Result of the creation: { client, invitation }. The wizard then shows the invitation link
const created = ref(null)
// API error for the wizard: { field, message }
const createError = ref(null)

// API error codes that belong to the client name (step 1 of the wizard)
const NAME_ERRORS = {
  ORGANIZATION_NAME_TAKEN: 'Ya hay un cliente con este nombre.',
  INVALID_NAME: 'Escribe el nombre del cliente.',
}

function startCreating() {
  created.value = null
  createError.value = null
  creating.value = true
}

function stopCreating() {
  creating.value = false
  created.value = null
}

// POST /api/organizations with first_site, then the first invitation (B4).
// If only the invitation fails, the client exists: the wizard says so and
// the invitation can be sent again from the client page
async function onCreate(data) {
  saving.value = true
  createError.value = null

  let client
  try {
    client = await organizationsStore.createOrganization(data)
  } catch (err) {
    createError.value = NAME_ERRORS[err?.code]
      ? { field: 'name', message: NAME_ERRORS[err.code] }
      : { field: null, message: err?.message || 'No se ha podido crear el cliente. Inténtalo de nuevo.' }
    saving.value = false
    return
  }

  let invitation = null
  try {
    const sent = await organizationsStore.createInvitation({
      email: data.user.email,
      organization_id: client.id,
    })
    // The contract has no name: the wizard shows the one typed in step 3
    invitation = { name: data.user.name, email: sent.email, link: sent.url, expires_at: sent.expires_at }
  } catch {
    invitation = null
  }

  created.value = { client, invitation }
  saving.value = false

  // The new client and its building appear in the list and the counters
  loadClients()
  organizationsStore.fetchCounts()
  sitesStore.fetchSites().catch(() => {})
}
</script>

<template>
  <AdminLayout>
    <!-- Sign-up wizard -->
    <div v-if="creating" class="max-w-3xl space-y-4">
      <button type="button" class="text-sm text-aqua-700 hover:underline" @click="stopCreating">
        ← Volver a clientes
      </button>
      <NewClientWizard
        :created="created"
        :submitting="saving"
        :server-error="createError"
        @submit="onCreate"
        @cancel="stopCreating"
        @open="openClient"
      />
    </div>

    <div v-else class="space-y-4">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <!-- Status filter: toggle buttons; aria-pressed tells screen readers which one is active -->
        <div role="group" aria-label="Filtrar por estado" class="flex flex-wrap gap-2">
          <button
            v-for="option in statusOptions"
            :key="option.label"
            type="button"
            class="min-h-9 rounded-full border px-4 text-sm font-semibold"
            :class="
              selectedStatus === option.value
                ? 'border-aqua-600 bg-aqua-600 text-white'
                : 'border-gray-300 bg-white text-gray-700 hover:border-aqua-600'
            "
            :aria-pressed="selectedStatus === option.value"
            @click="selectedStatus = option.value"
          >
            {{ option.label }} ({{ organizationsStore.counts[option.countKey] }})
          </button>
        </div>

        <button
          type="button"
          class="min-h-10 rounded-lg bg-aqua-600 px-4 text-sm font-semibold text-white hover:bg-aqua-700"
          @click="startCreating"
        >
          + Nuevo cliente
        </button>
      </div>

      <ClientsList
        v-model:search="search"
        v-model:page="page"
        v-model:pageSize="pageSize"
        :clients="organizationsStore.organizations"
        :total="organizationsStore.total"
        :page-sizes="PAGE_SIZES"
        :filtered="isFiltered"
        :sites-of="sitesOf"
        :loading="loading"
        :error="errorMessage"
        @select="openClient"
        @retry="loadClients"
      />
    </div>
  </AdminLayout>
</template>
