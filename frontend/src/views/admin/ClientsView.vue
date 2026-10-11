<!--
  ADMIN CLIENTS VIEW
  Lists client organizations with a status filter. Rendered inside AdminLayout.
  Uses temporary mock data until the organizations store exists (data area).
-->

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '../../layouts/AdminLayout.vue'
import ClientsList from '../../components/ClientsList.vue'
// TODO: replace with store data (data area) and delete this import
import { mockClients } from './mockClients'

const router = useRouter()

// Filter buttons. value matches OrganizationResponse.status; null means "all"
const statusOptions = [
  { value: null, label: 'Todos' },
  { value: 'TRIAL', label: 'En prueba' },
  { value: 'ACTIVE', label: 'Activos' },
  { value: 'SUSPENDED', label: 'Suspendidos' },
]

// Status currently selected; starts showing all clients
const selectedStatus = ref(null)

// Kept for the search step; not used to filter yet
const search = ref('')

// Clients after applying the status filter. Recomputed when selectedStatus changes
const filteredClients = computed(() => {
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
          {{ option.label }}
        </button>
      </div>

      <ClientsList
        v-model:search="search"
        :clients="filteredClients"
        :loading="false"
        error=""
        @select="openClient"
      />
    </div>
  </AdminLayout>
</template>