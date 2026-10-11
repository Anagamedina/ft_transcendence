<!--
  ADMIN CLIENTS VIEW
  Lists client organizations. Rendered inside AdminLayout.
  Uses temporary mock data until the organizations store exists (data area).
-->

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '../../layouts/AdminLayout.vue'
import ClientsList from '../../components/ClientsList.vue'
// TODO: replace the mock with store data (data area) and delete this import
import { mockClients } from './mockClients'

const router = useRouter()

// Kept for the search step; not used to filter yet
const search = ref('')

// Status filter options. value matches OrganizationResponse.status; null means "all"
const STATUS_FILTERS = [
  { value: null, label: 'Todos' },
  { value: 'TRIAL', label: 'En prueba' },
  { value: 'ACTIVE', label: 'Activos' },
  { value: 'SUSPENDED', label: 'Suspendidos' },
]

// Currently selected status (null = show every client)
const selectedStatus = ref(null)

// How many clients each filter would show, so every button can display its count
function countFor(status) {
  if (status === null) return mockClients.length
  return mockClients.filter((client) => client.status === status).length
}

// Clients that match the selected status
const clients = computed(() => {
  if (selectedStatus.value === null) return mockClients
  return mockClients.filter((client) => client.status === selectedStatus.value)
})

function openClient(client) {
  router.push(`/admin/clients/${client.id}`)
}
</script>

<template>
  <AdminLayout>
    <div class="space-y-4">
      <!-- Status filter: toggle buttons; aria-pressed tells screen readers which one is active -->
      <div role="group" aria-label="Filtrar por estado" class="flex flex-wrap gap-2">
        <button
          v-for="filter in STATUS_FILTERS"
          :key="filter.label"
          type="button"
          :aria-pressed="selectedStatus === filter.value"
          class="min-h-9 px-4 py-2 rounded-full border text-sm font-semibold transition-colors"
          :class="
            selectedStatus === filter.value
              ? 'bg-aqua-600 border-aqua-600 text-white'
              : 'bg-white border-gray-300 text-gray-700 hover:border-aqua-600 hover:text-aqua-600'
          "
          @click="selectedStatus = filter.value"
        >
          {{ filter.label }} ({{ countFor(filter.value) }})
        </button>
      </div>

      <ClientsList
        v-model:search="search"
        :clients="clients"
        :loading="false"
        error=""
        @select="openClient"
      />
    </div>
  </AdminLayout>
</template>