<!--
  CLIENTS LIST
  Presentational table of client organizations for the admin zone.
  Receives data via props only and emits events; the parent decides what to do.
-->

<template>
  <section class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
      <h2 class="text-lg font-bold text-gray-800">Clientes</h2>

      <!-- Search box: visual only. Filtering logic belongs to the parent view -->
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

    <!-- overflow-x-auto: on narrow screens the table scrolls inside its card, not the whole page -->
    <div v-else class="overflow-x-auto rounded-xl border border-gray-200 bg-white">
      <table class="w-full min-w-[760px] text-sm">
        <caption class="sr-only">Clientes</caption>
        <thead class="bg-gray-50 text-left text-gray-600">
          <tr>
            <!-- sticky left-0: the client name stays visible while the table scrolls sideways -->
            <th scope="col" class="sticky left-0 bg-gray-50 px-4 py-3 font-semibold">Cliente</th>
            <th scope="col" class="px-4 py-3 font-semibold">Estado</th>
            <th scope="col" class="px-4 py-3 font-semibold">Prueba</th>
            <th scope="col" class="px-4 py-3 font-semibold text-right">Edificios</th>
            <th scope="col" class="px-4 py-3 font-semibold text-right">Sensores</th>
            <th scope="col" class="px-4 py-3 font-semibold text-right">Usuarios</th>
            <th scope="col" class="px-4 py-3 font-semibold text-right">Alertas</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="{ client, status } in rows"
            :key="client.id"
            class="border-t border-gray-200"
          >
            <th scope="row" class="sticky left-0 bg-white px-4 py-3 text-left font-semibold">
              <!-- Button styled as a link: the parent decides where to navigate -->
              <button
                type="button"
                class="text-aqua-600 hover:text-aqua-900 hover:underline text-left"
                @click="$emit('select', client)"
              >
                {{ client.name }}
              </button>
            </th>
            <td class="px-4 py-3">
              <span class="inline-block whitespace-nowrap rounded-full px-3 py-1 text-xs font-semibold" :class="status.pillClass">
                {{ status.label }}
              </span>
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-gray-600">{{ status.trialText }}</td>
            <td class="px-4 py-3 text-right tabular-nums">{{ client.site_count }}</td>
            <td class="px-4 py-3 text-right tabular-nums">{{ client.sensor_count }}</td>
            <td class="px-4 py-3 text-right tabular-nums">{{ client.user_count }}</td>
            <!-- Red when at least one open alert is critical -->
            <td
              class="px-4 py-3 text-right tabular-nums font-bold"
              :class="client.critical_alerts > 0 ? 'text-red-700' : 'text-gray-800'"
            >
              {{ client.open_alerts }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import LoadingState from './LoadingState.vue'
import ErrorState from './ErrorState.vue'
import EmptyState from './EmptyState.vue'
import { useClientStatus } from '../composables/useClientStatus'

const props = defineProps({
  // Each client follows OrganizationResponse:
  // { id, name, status, trial_ends_at, site_count, sensor_count, user_count, open_alerts, critical_alerts, ... }
  clients: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  // Current search text (use with v-model:search in the parent)
  search: { type: String, default: '' },
})

defineEmits(['select', 'retry', 'update:search'])

// Pairs each client with its translated status, computed once per client
// instead of calling useClientStatus several times inside the template
const rows = computed(() =>
  props.clients.map((client) => ({ client, status: useClientStatus(client) }))
)
</script>