<!-- Temporary DocumentsView created for issue 159 before further changes-->

<template>
  <section class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-slate-900">Documentos</h1>
      <p class="mt-1 text-sm text-slate-600">
        Consulta los documentos de tus edificios.
      </p>
    </div>

    <div class="flex flex-wrap items-center justify-between gap-3">
      <p class="text-sm text-slate-600">
        {{ documentsStore.total }} documento(s)
      </p>

      <button
        type="button"
        class="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-50"
        :disabled="documentsStore.status === 'loading'"
        @click="loadDocuments"
      >
        Actualizar
      </button>
    </div>

    <LoadingState
      v-if="
        documentsStore.status === 'loading' || documentsStore.status === 'idle'
      "
      message="Cargando documentos…"
    />

    <ErrorState
      v-else-if="documentsStore.status === 'error'"
      title="No se han podido cargar los documentos"
      :message="documentsStore.error"
      @retry="loadDocuments"
    />

    <EmptyState
      v-else-if="documentsStore.items.length === 0"
      title="Todavía no hay documentos"
      icon="file-text"
    />

    <div
      v-else
      class="overflow-x-auto rounded-xl border border-slate-200 bg-white"
    >
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50 text-left text-xs uppercase text-slate-500">
          <tr>
            <th class="px-4 py-3">Documento</th>
            <th class="px-4 py-3">Tipo</th>
            <th class="px-4 py-3">Edificio</th>
            <th class="px-4 py-3">Fecha</th>
          </tr>
        </thead>

        <tbody class="divide-y divide-slate-100">
          <tr v-for="document in documentsStore.items" :key="document.id">
            <td class="px-4 py-3 font-medium text-slate-800">
              {{
                document.filename || document.name || `Documento ${document.id}`
              }}
            </td>
            <td class="px-4 py-3 text-slate-600">
              {{ document.kind || "—" }}
            </td>
            <td class="px-4 py-3 text-slate-600">
              {{ document.site_name || document.site_id || "—" }}
            </td>
            <td class="px-4 py-3 text-slate-600">
              {{ formatDate(document.created_at) }}
            </td>
          </tr>
        </tbody>
      </table>

      <div
        v-if="documentsStore.pages > 1"
        class="flex items-center justify-between border-t border-slate-200 px-4 py-3"
      >
        <button
          type="button"
          class="rounded-md border border-slate-300 px-3 py-2 text-sm disabled:opacity-40"
          :disabled="
            documentsStore.page <= 1 || documentsStore.status === 'loading'
          "
          @click="changePage(documentsStore.page - 1)"
        >
          Anterior
        </button>

        <span class="text-sm text-slate-600">
          Página {{ documentsStore.page }} de {{ documentsStore.pages }}
        </span>

        <button
          type="button"
          class="rounded-md border border-slate-300 px-3 py-2 text-sm disabled:opacity-40"
          :disabled="
            documentsStore.page >= documentsStore.pages ||
            documentsStore.status === 'loading'
          "
          @click="changePage(documentsStore.page + 1)"
        >
          Siguiente
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted } from "vue";
import { useDocumentsStore } from "../../stores/documents";
import LoadingState from "../../components/LoadingState.vue";
import ErrorState from "../../components/ErrorState.vue";
import EmptyState from "../../components/EmptyState.vue";

const documentsStore = useDocumentsStore();

async function loadDocuments(page = 1) {
  try {
    await documentsStore.fetchDocuments({ page });
  } catch {
    // El estado de error ya lo gestiona el store.
  }
}

async function changePage(page) {
  await loadDocuments(page);
}

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "—";

  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "medium",
  }).format(date);
}

onMounted(() => loadDocuments());
</script>
