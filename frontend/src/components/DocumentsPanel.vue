<!--
  DOCUMENTS PANEL (client)
  Documents of the client's buildings: list with filters, download, preview
  and delete (DocumentsTable). "Subir documento" opens a modal (FileDropzone):
  next to the title when there are documents, in the empty state when there
  are none, which also explains what documents are for (F27).
  Without `site`: all buildings, with the page title (/app/documents).
  With `site`: only that building, for its Documentos tab; the upload is
  already set to that building and there is no building filter.
  Data: documents store (B11) and sites store (B2).
  Usage:
    <DocumentsPanel />                 (DocumentsView)
    <DocumentsPanel :site="site" />    (BuildingView, ?tab=documentos)
-->

<template>
  <section class="space-y-6">
    <header class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 v-if="!site" class="text-2xl font-bold text-slate-900">Documentos</h1>
        <p class="text-sm text-slate-600" :class="{ 'mt-1': !site }">
          {{
            site
              ? `Planos, informes y facturas de ${site.name}.`
              : "Consulta, sube y descarga los documentos de tus edificios."
          }}
        </p>
      </div>
      <button
        v-if="hasDocuments"
        type="button"
        class="rounded-lg bg-aqua-600 px-4 py-2 text-sm font-semibold text-white hover:bg-aqua-700 focus:outline-none focus:ring-2 focus:ring-aqua-400 disabled:opacity-50"
        :disabled="!canUpload"
        @click="openUpload"
      >
        Subir documento
      </button>
    </header>

    <!-- Result of the last action; role="status" announces it to screen readers -->
    <p
      v-if="actionMessage"
      role="status"
      class="rounded-lg border border-success-light bg-success-light px-4 py-3 text-sm font-semibold text-success-dark"
    >
      {{ actionMessage }}
    </p>

    <p
      v-if="actionError"
      role="alert"
      class="rounded-lg border border-danger-light bg-danger-light px-4 py-3 text-sm font-semibold text-danger-dark"
    >
      {{ actionError }}
    </p>

    <LoadingState
      v-if="!initialLoadFinished"
      message="Cargando documentos…"
    />

    <ErrorState
      v-else-if="documentsStore.status === 'error'"
      title="No se han podido cargar los documentos"
      :message="documentsStore.error"
      @retry="loadDocuments(1)"
    />

    <!-- Nothing uploaded yet: explanation and upload button -->
    <EmptyState
      v-else-if="!hasDocuments"
      :title="
        site
          ? 'Este edificio todavía no tiene documentos'
          : 'Todavía no tienes documentos'
      "
      message="Guarda aquí los planos, informes y facturas de tus edificios para tenerlos a mano. Solo los ve tu organización y el equipo de AquaGuard."
      icon="building"
    >
      <template #action>
        <button
          type="button"
          class="rounded-lg bg-aqua-600 px-4 py-2 text-sm font-semibold text-white hover:bg-aqua-700 focus:outline-none focus:ring-2 focus:ring-aqua-400 disabled:opacity-50"
          :disabled="!canUpload"
          @click="openUpload"
        >
          Subir documento
        </button>
        <p v-if="!site && sitesStore.status === 'error'" class="mt-2 text-sm text-danger-dark">
          No se han podido cargar tus edificios.
          <button type="button" class="font-semibold underline" @click="loadSites">
            Reintentar
          </button>
        </p>
      </template>
    </EmptyState>

    <template v-else>
      <p class="text-sm text-slate-600">
        {{ documentsStore.total }}
        {{ documentsStore.total === 1 ? "documento" : "documentos" }}
      </p>
      <DocumentsTable
        :documents="documentsStore.items"
        :sites="uploadSites"
        :page="documentsStore.page"
        :pages="documentsStore.pages"
        @filters-change="applyFilters"
        @page-change="loadDocuments"
        @delete="handleDelete"
      />
    </template>

    <Modal :show="uploadOpen" title="Subir documento" @close="closeUpload">
      <!-- v-if: every opening starts with an empty form -->
      <FileDropzone
        v-if="uploadOpen"
        :sites="uploadSites"
        :uploading="uploading"
        :progress="uploadProgress"
        @upload="handleUpload"
        @cancel="closeUpload"
      />
      <p v-if="uploadError" role="alert" class="mt-3 text-sm text-danger-dark">
        {{ uploadError }}
      </p>
    </Modal>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useDocumentsStore } from "../stores/documents";
import { useSitesStore } from "../stores/sites";
import LoadingState from "./LoadingState.vue";
import ErrorState from "./ErrorState.vue";
import EmptyState from "./EmptyState.vue";
import Modal from "./Modal.vue";
import FileDropzone from "./FileDropzone.vue";
import DocumentsTable from "./DocumentsTable.vue";

const props = defineProps({
  // One building ({ id, name }) for its Documentos tab; null = all buildings
  site: { type: Object, default: null },
});

const documentsStore = useDocumentsStore();
const sitesStore = useSitesStore();

const initialLoadFinished = ref(false);
const filters = ref({});
const uploadOpen = ref(false);
const uploading = ref(false);
const uploadProgress = ref(0);
const uploadError = ref("");
const actionError = ref("");
const actionMessage = ref("");

const hasFilters = computed(() =>
  Object.values(filters.value).some((value) => value),
);
// A filter that hides everything still shows the table, not the empty state
const hasDocuments = computed(
  () => documentsStore.total > 0 || hasFilters.value,
);
// Buildings for the filter and the upload: only this one inside a building
const uploadSites = computed(() =>
  props.site ? [props.site] : sitesStore.sites,
);
// Uploading needs at least one building to attach the document to
const canUpload = computed(() => uploadSites.value.length > 0);

async function loadSites() {
  try {
    await sitesStore.fetchSites();
  } catch {
    // The store keeps the error; the template shows it
  }
}

async function loadDocuments(page = 1) {
  try {
    await documentsStore.fetchDocuments({
      page,
      ...filters.value,
      // Inside a building the list is always that building
      ...(props.site ? { site_id: props.site.id } : {}),
    });
  } catch {
    // The store keeps the error; the template shows it
  } finally {
    initialLoadFinished.value = true;
  }
}

function applyFilters(nextFilters) {
  filters.value = nextFilters;
  loadDocuments(1);
}

function openUpload() {
  uploadError.value = "";
  actionMessage.value = "";
  uploadOpen.value = true;
}

function closeUpload() {
  // The upload keeps going in the background if the modal is closed now
  if (uploading.value) return;
  uploadOpen.value = false;
}

async function handleUpload(payload) {
  uploading.value = true;
  uploadProgress.value = 0;
  uploadError.value = "";

  try {
    await documentsStore.uploadDocument(payload, {
      onUploadProgress(event) {
        if (event.total) {
          uploadProgress.value = Math.round((event.loaded / event.total) * 100);
        }
      },
    });
    uploading.value = false;
    uploadOpen.value = false;
    actionMessage.value = `Documento «${payload.file.name}» subido.`;
    await loadDocuments(1);
  } catch (error) {
    uploadError.value = error.message || "No se pudo subir el documento.";
  } finally {
    uploading.value = false;
    uploadProgress.value = 0;
  }
}

async function handleDelete(doc) {
  actionError.value = "";
  actionMessage.value = "";

  try {
    await documentsStore.deleteDocument(doc.id);
    actionMessage.value = `Documento «${doc.filename}» eliminado.`;
    await loadDocuments(documentsStore.page);
  } catch (error) {
    actionError.value = error.message || "No se pudo eliminar el documento.";
  }
}

onMounted(async () => {
  // Clears the list of another organization the store may still hold
  documentsStore.reset();
  // A building tab already has its building: no need to load the list
  await Promise.all([props.site ? null : loadSites(), loadDocuments()]);
});
</script>
