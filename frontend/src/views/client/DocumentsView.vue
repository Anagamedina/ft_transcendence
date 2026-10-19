
<template>
  <section class="space-y-6">
    <header>
      <h1 class="text-2xl font-bold text-slate-900">Documentos</h1>
      <p class="mt-1 text-sm text-slate-600">
        Consulta, sube y descarga documentos de tus edificios.
      </p>
    </header>

    <ErrorState
      v-if="sitesStore.status === 'error'"
      title="No se han podido cargar los edificios"
      :message="sitesStore.error"
      @retry="loadSites"
    />

    <FileDropzone
      v-else
      :sites="sitesStore.sites"
      :uploading="uploading"
      :progress="uploadProgress"
      @upload="handleUpload"
    />

    <p
      v-if="actionMessage"
      role="status"
      class="rounded-md bg-green-50 px-4 py-3 text-sm text-green-800"
    >
      {{ actionMessage }}
    </p>

    <ErrorState
      v-if="actionError"
      title="No se ha podido completar la operación"
      :message="actionError"
      @retry="loadDocuments"
    />

    <div class="flex flex-wrap items-center justify-between gap-3">
      <p class="text-sm text-slate-600">
        {{ documentsStore.total }} documento(s)
      </p>
    </div>

    <LoadingState
     v-if="
        !initialLoadFinished &&
        (
        documentsStore.status === 'loading' ||
        documentsStore.status === 'idle'
        )
     "
     message="Cargando documentos…"
    />

    <ErrorState
      v-else-if="documentsStore.status === 'error'"
      title="No se han podido cargar los documentos"
      :message="documentsStore.error"
      @retry="loadDocuments(1)"
    />

    <DocumentsTable
      v-else
      :documents="documentsStore.items"
      :sites="sitesStore.sites"
      :page="documentsStore.page"
      :pages="documentsStore.pages"
      @filters-change="applyFilters"
      @page-change="changePage"
      @delete="handleDelete"
    />
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useDocumentsStore } from "../../stores/documents";
import { useSitesStore } from "../../stores/sites";
import LoadingState from "../../components/LoadingState.vue";
import ErrorState from "../../components/ErrorState.vue";
import FileDropzone from "../../components/FileDropzone.vue";
import DocumentsTable from "../../components/DocumentsTable.vue";

const documentsStore = useDocumentsStore();
const sitesStore = useSitesStore();

const uploading = ref(false);
const uploadProgress = ref(0);
const actionError = ref("");
const actionMessage = ref("");
const initialLoadFinished = ref(false);

const filters = ref({});

async function loadSites() {
  try {
    await sitesStore.fetchSites();
  } catch {
    // L'erreur est exposée par le store.
  }
}

async function loadDocuments(page = 1) {
  actionError.value = "";

  try {
    await documentsStore.fetchDocuments({
      page,
      ...filters.value,
    });
  } catch {
    // L'erreur est exposée par le store.
  } finally {
    initialLoadFinished.value = true;
  }
}

async function applyFilters(nextFilters) {
  filters.value = nextFilters;
  await loadDocuments(1);
}

async function changePage(page) {
  await loadDocuments(page);
}

async function handleUpload(payload) {
  uploading.value = true;
  uploadProgress.value = 0;
  actionError.value = "";
  actionMessage.value = "";

  try {
    await documentsStore.uploadDocument(payload, {
      onUploadProgress(event) {
        if (event.total) {
          uploadProgress.value = Math.round(
            (event.loaded / event.total) * 100,
          );
        }
      },
    });

    actionMessage.value = "Documento subido correctamente.";
    await loadDocuments(1);
  } catch (error) {
    actionError.value =
      error.message || "No se pudo subir el documento.";
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
    actionMessage.value = "Documento eliminado correctamente.";
    await loadDocuments(documentsStore.page);
  } catch (error) {
    actionError.value =
      error.message || "No se pudo eliminar el documento.";
  }
}

onMounted(async () => {
  await Promise.all([loadSites(), loadDocuments()]);
});
</script>
