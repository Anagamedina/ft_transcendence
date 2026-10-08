<!--
  ADMIN CLIENT DETAIL VIEW
  Shows one client organization and its sites. Rendered inside AdminLayout.
  Uses temporary mock data until the organizations and sites stores exist (data area).
-->

<script setup>
import { computed } from 'vue'
import AdminLayout from '../../layouts/AdminLayout.vue'
import SitesSummary from '../../components/SitesSummary.vue'
import EmptyState from '../../components/EmptyState.vue'
// TODO: replace both mocks with store data (data area) and delete these imports
import { mockClients } from './mockClients'
import { sites as mockSites } from '../../services/fixtures/sites'

const props = defineProps({
  // Comes from the route /admin/clients/:id (router option props: true)
  id: { type: String, required: true },
})

const client = computed(() => mockClients.find((c) => c.id === props.id))

const clientSites = computed(() =>
  mockSites.filter((site) => site.organization_id === props.id)
)

function formatDate(isoDate) {
  return new Date(isoDate).toLocaleDateString('es-ES')
}
</script>

<template>
  <AdminLayout>
    <div class="p-6 space-y-6">
      <router-link to="/admin/clients" class="text-sm text-aqua-700 hover:underline">
        ← Volver a clientes
      </router-link>

      <EmptyState
        v-if="!client"
        title="Cliente no encontrado"
        message="Puede que se haya eliminado o que el enlace no sea correcto."
        icon="building"
      />

      <template v-else>
        <header>
          <h1 class="text-2xl font-bold text-gray-900">{{ client.name }}</h1>
          <p class="text-sm text-gray-500">Cliente desde {{ formatDate(client.created_at) }}</p>
        </header>

        <SitesSummary :sites="clientSites" />
      </template>
    </div>
  </AdminLayout>
</template>