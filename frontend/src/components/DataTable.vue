<!--
  DATA TABLE
  Shared admin table: search box, filter selects, "Limpiar filtros",
  loading / error / empty states, "Por página 10/25" and pagination.
  It filters and paginates the rows it receives; the parent only renders
  each row through the #row slot (one <tr> per row). No HTTP calls.
  Usage:
    <DataTable
      :columns="[{ key: 'name', label: 'Sensor' }]"
      :rows="sensors"
      :search-fields="['name', 'location']"
      :filters="[{ key: 'status', label: 'Estado', allLabel: 'Todos los estados',
                   options: [{ value: 'ONLINE', label: 'Conectado' }] }]"
      :loading="isLoading"
      :error="errorMessage"
      item-name="sensores"
      @retry="loadSensors"
    >
      <template #row="{ row }"><tr>...</tr></template>
    </DataTable>
-->

<template>
  <div class="space-y-4">
    <!-- Search and filters. flex-wrap: on tablets the selects drop to a second
         line instead of pushing the page wider than the screen -->
    <div class="flex flex-wrap gap-3 rounded-xl border border-slate-200 bg-white p-4">
      <input
        v-model.trim="search"
        type="search"
        :placeholder="searchPlaceholder"
        :aria-label="searchPlaceholder"
        class="w-full min-w-0 rounded-lg border border-slate-300 px-3 py-2 text-sm xl:w-auto xl:min-w-64 xl:flex-1"
      />

      <select
        v-for="filter in filters"
        :key="filter.key"
        v-model="filterValues[filter.key]"
        :aria-label="`Filtrar por ${filter.label.toLowerCase()}`"
        class="min-w-0 flex-1 basis-full rounded-lg border border-slate-300 px-3 py-2 text-sm sm:basis-auto xl:flex-none"
      >
        <option value="ALL">{{ filter.allLabel }}</option>
        <option v-for="option in filter.options" :key="option.value" :value="option.value">
          {{ option.label }}
        </option>
      </select>

      <button
        type="button"
        class="w-full whitespace-nowrap rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-slate-100 sm:w-auto"
        @click="resetFilters"
      >
        Limpiar filtros
      </button>
    </div>

    <LoadingState v-if="loading" :message="`Cargando ${itemName}…`" />

    <ErrorState v-else-if="error" :message="error" @retry="$emit('retry')" />

    <!-- Two empty cases: nothing at all, or nothing matching the search/filters -->
    <EmptyState
      v-else-if="rows.length === 0"
      :title="emptyTitle"
      :message="emptyMessage"
      :icon="icon"
    />

    <EmptyState
      v-else-if="filteredRows.length === 0"
      title="No hay resultados"
      message="Prueba a cambiar la búsqueda o los filtros."
      :icon="icon"
    >
      <template #action>
        <button
          type="button"
          class="text-sm font-medium text-aqua-800 underline"
          @click="resetFilters"
        >
          Limpiar filtros
        </button>
      </template>
    </EmptyState>

    <div v-else class="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table class="min-w-full divide-y divide-slate-200 text-left text-sm">
        <caption v-if="caption" class="sr-only">{{ caption }}</caption>
        <thead class="bg-slate-50 text-slate-600">
          <tr>
            <th v-for="column in columns" :key="column.key" scope="col" class="px-4 py-3 font-medium">
              {{ column.label }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <template v-for="row in pageRows" :key="row[rowKey]">
            <slot name="row" :row="row" />
          </template>
        </tbody>
      </table>

      <!-- Page size, visible range and page buttons -->
      <div
        class="flex flex-col gap-3 border-t border-slate-100 px-4 py-3 text-sm text-slate-600 sm:flex-row sm:items-center sm:justify-between"
      >
        <label class="flex items-center gap-2">
          Por página
          <select
            v-model.number="pageSize"
            class="rounded-lg border border-slate-300 px-2 py-1 text-sm"
          >
            <option v-for="size in pageSizes" :key="size" :value="size">{{ size }}</option>
          </select>
        </label>

        <!-- aria-live: screen readers announce the new range when the page changes -->
        <p aria-live="polite" class="tabular-nums">
          {{ rangeStart }}–{{ rangeEnd }} de {{ filteredRows.length }} {{ itemName }}
        </p>

        <nav v-if="pageCount > 1" aria-label="Paginación" class="flex flex-wrap gap-1">
          <button
            type="button"
            :class="pageButtonClass(false)"
            :disabled="page <= 1"
            @click="page -= 1"
          >
            Anterior
          </button>
          <button
            v-for="number in pageCount"
            :key="number"
            type="button"
            :class="pageButtonClass(number === page)"
            :aria-current="number === page ? 'page' : undefined"
            @click="page = number"
          >
            {{ number }}
          </button>
          <button
            type="button"
            :class="pageButtonClass(false)"
            :disabled="page >= pageCount"
            @click="page += 1"
          >
            Siguiente
          </button>
        </nav>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import LoadingState from './LoadingState.vue'
import ErrorState from './ErrorState.vue'
import EmptyState from './EmptyState.vue'

const props = defineProps({
  // Table headers: [{ key: 'name', label: 'Sensor' }, ...]
  columns: { type: Array, required: true },
  // All the rows; this component filters and paginates them
  rows: { type: Array, default: () => [] },
  // Field used as the v-for key of each row
  rowKey: { type: String, default: 'id' },
  // Row fields the search box looks into
  searchFields: { type: Array, default: () => [] },
  searchPlaceholder: { type: String, default: 'Buscar…' },
  // Filter selects: [{ key, label, allLabel, options: [{ value, label }], match? }]
  // By default a row matches when row[key] === selected value;
  // match(row, value) replaces that rule when the filter needs something else.
  filters: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  // Error message; empty string when there is no error
  error: { type: String, default: '' },
  // Plural name used in texts: "Cargando sensores…", "1–10 de 23 sensores"
  itemName: { type: String, default: 'elementos' },
  emptyTitle: { type: String, default: 'No hay datos todavía' },
  emptyMessage: { type: String, default: '' },
  // Any icon name supported by AppIcon (building, droplet, wifi, alert, bar-chart)
  icon: { type: String, default: 'droplet' },
  // Hidden table title for screen readers
  caption: { type: String, default: '' },
  pageSizes: { type: Array, default: () => [10, 25] },
})

defineEmits(['retry'])

// ---------------------------------------------------------------------------
// Search and filters
// ---------------------------------------------------------------------------
const search = ref('')
// Selected value of each filter, by filter key ('ALL' = no filter)
const filterValues = reactive({})

// Filters can arrive later (e.g. options built from loaded data): start them at 'ALL'
watch(
  () => props.filters.map((filter) => filter.key),
  (keys) => {
    for (const key of keys) {
      if (!(key in filterValues)) filterValues[key] = 'ALL'
    }
  },
  { immediate: true }
)

function resetFilters() {
  search.value = ''
  for (const filter of props.filters) filterValues[filter.key] = 'ALL'
}

const filteredRows = computed(() => {
  const query = search.value.toLocaleLowerCase()

  return props.rows.filter((row) => {
    const matchesSearch =
      !query ||
      props.searchFields.some((field) =>
        String(row[field] ?? '').toLocaleLowerCase().includes(query)
      )

    const matchesFilters = props.filters.every((filter) => {
      const value = filterValues[filter.key]
      if (value === undefined || value === 'ALL') return true
      return filter.match ? filter.match(row, value) : row[filter.key] === value
    })

    return matchesSearch && matchesFilters
  })
})

// ---------------------------------------------------------------------------
// Pagination
// ---------------------------------------------------------------------------
const page = ref(1)
const pageSize = ref(props.pageSizes[0])

const pageCount = computed(() =>
  Math.max(1, Math.ceil(filteredRows.value.length / pageSize.value))
)

// Back to the first page whenever the search, a filter or the page size changes
watch([search, filterValues, pageSize], () => {
  page.value = 1
})

// Keep the page in range when rows disappear (e.g. the last row of a page is removed)
watch(pageCount, (count) => {
  if (page.value > count) page.value = count
})

const pageRows = computed(() =>
  filteredRows.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value)
)

// Range shown in "1–10 de 23"
const rangeStart = computed(() =>
  filteredRows.value.length === 0 ? 0 : (page.value - 1) * pageSize.value + 1
)
const rangeEnd = computed(() =>
  Math.min(page.value * pageSize.value, filteredRows.value.length)
)

// Same look as the ClientsList pagination; the current page is filled in aqua
function pageButtonClass(isCurrent) {
  const base =
    'min-h-9 min-w-9 rounded-lg border px-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50'
  return isCurrent
    ? `${base} border-aqua-600 bg-aqua-600 text-white`
    : `${base} border-gray-300 bg-white text-gray-700 hover:border-aqua-600`
}
</script>