<!--
  CLIENTS LIST
  Presentational list of client organizations for the admin zone.
  Receives data via props only and emits events; the parent decides what to do.
-->

<template>
  <section class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
      <h2 class="text-lg font-bold text-gray-800">Clientes</h2>

      <!-- Search box: visual only. Filtering logic belongs to the data/state area -->
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

    <ErrorState
      v-else-if="error"
      :message="error"
      @retry="$emit('retry')"
    />

    <EmptyState
      v-else-if="clients.length === 0"
      title="No hay clientes todavía"
      message="Cuando des de alta un cliente aparecerá aquí."
      icon="building"
    />

    <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <Card
        v-for="client in clients"
        :key="client.id"
        :title="client.name"
        :description="sitesLabel(client.sites_count)"
        button-text="Ver sites"
        @click="$emit('select', client)"
      />
    </div>
  </section>
</template>

<script setup>
import Card from './Card.vue'
import LoadingState from './LoadingState.vue'
import ErrorState from './ErrorState.vue'
import EmptyState from './EmptyState.vue'

defineProps({
  // Each client: { id, name, created_at, sites_count? }
  clients: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  // Current search text (use with v-model:search in the parent)
  search: { type: String, default: '' },
})

defineEmits(['select', 'retry', 'update:search'])

// Builds the card description; sites_count is optional until the API provides it
function sitesLabel(count) {
  if (count === undefined) return ''
  return count === 1 ? '1 site' : `${count} sites`
}
</script>