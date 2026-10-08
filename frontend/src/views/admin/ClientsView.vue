<!--
  ADMIN CLIENTS VIEW
  Lists client organizations. Rendered inside AdminLayout.
  Uses temporary mock data until the organizations store exists (#121 / data area).
-->

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '../../layouts/AdminLayout.vue'
import ClientsList from '../../components/ClientsList.vue'
// TODO: replace both mocks with store data (data area) and delete these imports
import { mockClients } from './mockClients'
import { sites as mockSites } from '../../services/fixtures/sites'

const router = useRouter()

// Kept for the future filters; not used to filter yet
const search = ref('')

// Adds how many sites each client has, so the card can show it
const clients = computed(() =>
  mockClients.map((client) => ({
    ...client,
    sites_count: mockSites.filter((site) => site.organization_id === client.id).length,
  }))
)

function openClient(client) {
  router.push(`/admin/clients/${client.id}`)
}
</script>

<template>
  <AdminLayout>
    <div>
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