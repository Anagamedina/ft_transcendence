<!--
  ADMIN CLIENTS VIEW
  Lists client organizations with a status filter, search, pagination and
  expandable buildings; "+ Nuevo cliente" opens the sign-up wizard on the same page.
  Rendered inside AdminLayout.
  Uses temporary mock data until the organizations store exists (data area).
-->

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '../../layouts/AdminLayout.vue'
import ClientsList from '../../components/ClientsList.vue'
import NewClientWizard from '../../components/NewClientWizard.vue'
// TODO: replace with store data and actions (data area) and delete this import
import { mockClients, sitesOf, createClient } from './mockClients'

const router = useRouter()

// Filter buttons. value matches OrganizationResponse.status; null means "all"
const statusOptions = [
  { value: null, label: 'Todos' },
  { value: 'TRIAL', label: 'En prueba' },
  { value: 'ACTIVE', label: 'Activos' },
  { value: 'SUSPENDED', label: 'Suspendidos' },
]

// Page sizes offered to the admin (the API accepts up to 100)
const PAGE_SIZES = [10, 25]

// Everything the admin can change in the list. These four values are exactly
// the query params of GET /api/organizations: status, q, page and page_size
const selectedStatus = ref(null)
const search = ref('')
const page = ref(1)
const pageSize = ref(PAGE_SIZES[0])

// How many clients each filter would show, so every button can display its count
function countFor(status) {
  if (status === null) return mockClients.length
  return mockClients.filter((client) => client.status === status).length
}

// Lowercase text for searching ('es' handles Spanish/Catalan letters correctly)
function normalize(text) {
  return text.toLocaleLowerCase('es')
}

// TODO: replace with the organizations store call (data area).
// Mimics GET /api/organizations on the mock data: filters, then cuts one page,
// and returns the same Page shape as the API { items, total, page, page_size, pages },
// so swapping it for the real call later does not change the template.
function queryMockClients({ status, q, page, pageSize }) {
  const text = normalize(q.trim())

  const matches = mockClients.filter((client) => {
    if (status !== null && client.status !== status) return false
    if (text === '') return true
    // Same fields the backend searches: name, city, legal name and tax id
    return [client.name, client.city, client.legal_name, client.tax_id].some(
      (field) => field && normalize(field).includes(text)
    )
  })

  const start = (page - 1) * pageSize
  return {
    items: matches.slice(start, start + pageSize),
    total: matches.length,
    page,
    page_size: pageSize,
    pages: Math.ceil(matches.length / pageSize),
  }
}

// Current page of results. Recomputed when any of the four values changes
const result = computed(() =>
  queryMockClients({
    status: selectedStatus.value,
    q: search.value,
    page: page.value,
    pageSize: pageSize.value,
  })
)

// A new filter, search or page size changes the results: go back to page 1,
// otherwise the admin could stay on a page that no longer exists
watch([selectedStatus, search, pageSize], () => {
  page.value = 1
})

// True when something hides clients, so the empty state can say "no matches"
const isFiltered = computed(() => selectedStatus.value !== null || search.value.trim() !== '')

function openClient(client) {
  router.push(`/admin/clients/${client.id}`)
}

// ---------------------------------------------------------------------------
// New client wizard. Shown instead of the list, on the same route
// ---------------------------------------------------------------------------
const creating = ref(false)
// Result of the creation: { client, invitation }. The wizard then shows the invitation link
const created = ref(null)

// The API rejects a repeated name, so the wizard checks it before sending
const existingNames = computed(() => mockClients.map((client) => client.name))

function startCreating() {
  created.value = null
  creating.value = true
}

function stopCreating() {
  creating.value = false
  created.value = null
}

// TODO: replace with the store action (POST /api/organizations with first_site, then B4 invitation)
function onCreate(data) {
  created.value = createClient(data)
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
        :existing-names="existingNames"
        :created="created"
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
            {{ option.label }} ({{ countFor(option.value) }})
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
        :clients="result.items"
        :total="result.total"
        :page-sizes="PAGE_SIZES"
        :filtered="isFiltered"
        :sites-of="sitesOf"
        :loading="false"
        error=""
        @select="openClient"
      />
    </div>
  </AdminLayout>
</template>
