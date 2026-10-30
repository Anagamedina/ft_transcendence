<!--
  CLIENT DOCUMENTS PANEL
  "Documentos" tab of the admin client detail: the documents of one organization
  (plans, reports, invoices, photos), with download, preview and delete.
  Data: documents store (B11, GET /api/documents?organization_id=).
  Reuses DocumentsTable, the same table the client sees in /app/documentos.
  Loads the list when it is mounted, which is every time the tab opens.
  Usage:
    <ClientDocumentsPanel :organization-id="client.id" :sites="clientSites" />
-->

<template>
  <section
    class="rounded-xl border border-slate-200 bg-white p-5"
    aria-labelledby="client-documents-title"
  >
    <header class="mb-4">
      <h2 id="client-documents-title" class="font-bold text-slate-900">
        Documentos
        <span v-if="loaded" class="font-normal text-slate-600"
          >({{ documentsStore.total }})</span
        >
      </h2>
      <p class="text-sm text-slate-600">
        Planos, informes y facturas de sus edificios.
      </p>
    </header>

    <LoadingState
      v-if="!loaded && documentsStore.status !== 'error'"
      message="Cargando documentos…"
    />

    <ErrorState
      v-else-if="documentsStore.status === 'error'"
      title="No se han podido cargar los documentos"
      :message="documentsStore.error"
      @retry="load(1)"
    />

    <!-- Empty only when there is nothing at all, not when a filter hides everything -->
    <EmptyState
      v-else-if="documentsStore.total === 0 && !hasFilters"
      title="Todavía no hay documentos"
      message="Aquí aparecerán los planos, informes y facturas de sus edificios."
      icon="building"
      compact
    />

    <DocumentsTable
      v-else
      :documents="documentsStore.items"
      :sites="sites"
      :page="documentsStore.page"
      :pages="documentsStore.pages"
      @filters-change="applyFilters"
      @page-change="load"
      @delete="remove"
    />

    <!-- Result of the last action; role="status" announces it to screen readers -->
    <p
      v-if="feedback"
      role="status"
      class="mt-2 text-sm font-semibold"
      :class="feedbackIsError ? 'text-danger-dark' : 'text-success-dark'"
    >
      {{ feedback }}
    </p>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import DocumentsTable from "./DocumentsTable.vue";
import LoadingState from "./LoadingState.vue";
import ErrorState from "./ErrorState.vue";
import EmptyState from "./EmptyState.vue";
import { useDocumentsStore } from "../stores/documents";

const props = defineProps({
  // Organization whose documents are listed
  organizationId: { type: String, required: true },
  // Buildings of this client, for the "Edificio" filter of the table
  sites: { type: Array, default: () => [] },
});

const documentsStore = useDocumentsStore();

const loaded = ref(false);
const filters = ref({});
const feedback = ref("");
const feedbackIsError = ref(false);

const hasFilters = computed(() =>
  Object.values(filters.value).some((value) => value),
);

// The organization_id filter is always sent, so the admin only sees this client
async function load(page = 1) {
  try {
    await documentsStore.fetchDocuments({
      page,
      ...filters.value,
      organization_id: props.organizationId,
    });
  } catch {
    // The store keeps the error; the template shows it
  } finally {
    loaded.value = true;
  }
}

function applyFilters(nextFilters) {
  filters.value = nextFilters;
  load(1);
}

async function remove(doc) {
  feedback.value = "";
  try {
    await documentsStore.deleteDocument(doc.id);
    feedbackIsError.value = false;
    feedback.value = `Documento «${doc.filename}» eliminado.`;
    await load(documentsStore.page);
  } catch (error) {
    feedbackIsError.value = true;
    feedback.value = error.message || "No se pudo eliminar el documento.";
  }
}

onMounted(() => {
  // Clears the list of another client the store may still hold
  documentsStore.reset();
  load(1);
});
</script>
