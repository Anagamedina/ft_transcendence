<!--
  DOCUMENTS TABLE
  List of documents with building and type filters, download, preview,
  delete and pagination. Used by the client (DocumentsPanel, in Documentos and
  in the Documentos tab of a building) and by the admin client detail
  (ClientDocumentsPanel). The building filter only shows with several buildings.
  Table from 1024 px up (the sidebar takes room from 768 px); one card per document below, so there is no
  horizontal scroll on a phone (F27).
  Usage:
    <DocumentsTable :documents="items" :sites="sites" :page="page" :pages="pages"
      @filters-change="..." @page-change="..." @delete="..." />
-->

<template>
  <section class="space-y-4">
    <div class="grid gap-3 sm:flex sm:flex-wrap">
      <!-- Only with several buildings: a building tab passes just its own -->
      <label v-if="sites.length > 1" class="block text-sm font-medium text-slate-700">
        Edificio
        <select
          v-model="siteId"
          class="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 sm:w-56"
          @change="emitFilters"
        >
          <option value="">Todos los edificios</option>
          <option v-for="site in sites" :key="site.id" :value="site.id">
            {{ site.name }}
          </option>
        </select>
      </label>

      <label class="block text-sm font-medium text-slate-700">
        Tipo
        <select
          v-model="kind"
          class="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 sm:w-44"
          @change="emitFilters"
        >
          <option value="">Todos los tipos</option>
          <option v-for="(label, value) in KIND_LABELS" :key="value" :value="value">
            {{ label }}
          </option>
        </select>
      </label>
    </div>

    <p
      v-if="documents.length === 0"
      class="rounded-xl border border-slate-200 bg-white px-4 py-8 text-center text-sm text-slate-600"
    >
      No hay documentos con estos filtros.
    </p>

    <template v-else>
      <!-- Phone and tablet: one card per document -->
      <ul class="space-y-3 lg:hidden">
        <li
          v-for="doc in documents"
          :key="doc.id"
          class="rounded-xl border border-slate-200 bg-white p-4"
        >
          <p class="break-words font-semibold text-slate-900">
            {{ docName(doc) }}
          </p>
          <p class="mt-1 text-sm text-slate-600">
            {{ kindLabel(doc.kind) }} · {{ doc.site_name || "—" }} ·
            {{ formatDate(doc.created_at) }}
          </p>
          <div class="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-sm font-semibold">
            <button
              type="button"
              class="text-aqua-700 hover:underline disabled:opacity-50"
              :disabled="busyId === doc.id"
              @click="download(doc)"
            >
              Descargar
            </button>
            <button
              v-if="isPreviewable(doc)"
              type="button"
              class="text-aqua-700 hover:underline disabled:opacity-50"
              :disabled="busyId === doc.id"
              @click="preview(doc)"
            >
              Vista previa
            </button>
            <button
              v-if="doc.can_delete === true"
              type="button"
              class="text-danger-dark hover:underline disabled:opacity-50"
              :disabled="busyId === doc.id"
              @click="remove(doc)"
            >
              Eliminar
            </button>
          </div>
        </li>
      </ul>

      <!-- Desktop: table -->
      <div
        class="hidden overflow-hidden rounded-xl border border-slate-200 bg-white lg:block"
      >
        <table class="min-w-full divide-y divide-slate-200 text-sm">
          <thead class="bg-slate-50 text-left text-xs uppercase text-slate-600">
            <tr>
              <th scope="col" class="px-4 py-3">Documento</th>
              <th scope="col" class="px-4 py-3">Tipo</th>
              <th scope="col" class="px-4 py-3">Edificio</th>
              <th scope="col" class="px-4 py-3">Fecha</th>
              <th scope="col" class="px-4 py-3">
                <span class="sr-only">Acciones</span>
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="doc in documents" :key="doc.id">
              <td class="break-all px-4 py-3 font-medium text-slate-900">
                {{ docName(doc) }}
              </td>
              <td class="px-4 py-3 text-slate-700">
                {{ kindLabel(doc.kind) }}
              </td>
              <td class="px-4 py-3 text-slate-700">
                {{ doc.site_name || "—" }}
              </td>
              <td class="whitespace-nowrap px-4 py-3 text-slate-700">
                {{ formatDate(doc.created_at) }}
              </td>
              <td class="px-4 py-3">
                <div class="flex flex-wrap justify-end gap-x-3 gap-y-1 font-semibold">
                  <button
                    type="button"
                    class="text-aqua-700 hover:underline disabled:opacity-50"
                    :disabled="busyId === doc.id"
                    @click="download(doc)"
                  >
                    Descargar
                  </button>
                  <button
                    v-if="isPreviewable(doc)"
                    type="button"
                    class="text-aqua-700 hover:underline disabled:opacity-50"
                    :disabled="busyId === doc.id"
                    @click="preview(doc)"
                  >
                    Vista previa
                  </button>
                  <button
                    v-if="doc.can_delete === true"
                    type="button"
                    class="text-danger-dark hover:underline disabled:opacity-50"
                    :disabled="busyId === doc.id"
                    @click="remove(doc)"
                  >
                    Eliminar
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <div
      v-if="pages > 1"
      class="flex items-center justify-between gap-3"
    >
      <button
        type="button"
        class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-40"
        :disabled="page <= 1"
        @click="$emit('page-change', page - 1)"
      >
        Anterior
      </button>
      <span class="text-sm text-slate-600">
        Página {{ page }} de {{ pages }}
      </span>
      <button
        type="button"
        class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-40"
        :disabled="page >= pages"
        @click="$emit('page-change', page + 1)"
      >
        Siguiente
      </button>
    </div>

    <!-- Preview of a PDF or an image, in the shared modal -->
    <Modal :show="Boolean(previewUrl)" :title="previewName" size="lg" @close="closePreview">
      <img
        v-if="previewType.startsWith('image/')"
        :src="previewUrl"
        :alt="previewName"
        class="mx-auto max-h-[70vh] max-w-full object-contain"
      />
      <iframe
        v-else-if="previewType === 'application/pdf'"
        :src="previewUrl"
        :title="previewName"
        class="h-[70vh] w-full"
      />
    </Modal>

    <p v-if="actionError" role="alert" class="text-sm text-danger-dark">
      {{ actionError }}
    </p>
  </section>
</template>

<script setup>
import { onBeforeUnmount, ref } from "vue";
import Modal from "./Modal.vue";
import { useDocumentsStore } from "../stores/documents";
// API dates are UTC; formatDate shows them in the user's local time
import { formatDate } from "../composables/useFormat";

defineProps({
  documents: { type: Array, default: () => [] },
  sites: { type: Array, default: () => [] },
  page: { type: Number, default: 1 },
  pages: { type: Number, default: 0 },
});

const emit = defineEmits(["filters-change", "page-change", "delete"]);
const documentsStore = useDocumentsStore();

// Document types of the API (B11) in client language
const KIND_LABELS = {
  PLAN: "Plano",
  REPORT: "Informe",
  INVOICE: "Factura",
  PHOTO: "Foto",
  OTHER: "Otro",
};

const siteId = ref("");
const kind = ref("");
const busyId = ref(null);
const actionError = ref("");
const previewUrl = ref("");
const previewType = ref("");
const previewName = ref("");

function emitFilters() {
  emit("filters-change", {
    site_id: siteId.value || undefined,
    kind: kind.value || undefined,
  });
}

function kindLabel(value) {
  return KIND_LABELS[value] || "Otro";
}

function docName(doc) {
  return doc.filename || doc.name || "Documento";
}

function isPreviewable(doc) {
  return ["application/pdf", "image/jpeg", "image/png"].includes(
    doc.content_type,
  );
}

async function getBlob(doc) {
  const response = await documentsStore.downloadDocument(doc.id);
  return response.data instanceof Blob
    ? response.data
    : new Blob([response.data], { type: doc.content_type });
}

function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename || "documento";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

async function download(doc) {
  busyId.value = doc.id;
  actionError.value = "";
  try {
    const blob = await getBlob(doc);
    saveBlob(blob, doc.filename);
  } catch (error) {
    actionError.value = error.message || "No se pudo descargar el documento.";
  } finally {
    busyId.value = null;
  }
}

async function preview(doc) {
  busyId.value = doc.id;
  actionError.value = "";
  try {
    const blob = await getBlob(doc);
    closePreview();
    previewUrl.value = URL.createObjectURL(blob);
    previewType.value = doc.content_type;
    previewName.value = docName(doc);
  } catch (error) {
    actionError.value = error.message || "No se pudo abrir la vista previa.";
  } finally {
    busyId.value = null;
  }
}

function closePreview() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
  previewUrl.value = "";
  previewType.value = "";
  previewName.value = "";
}

function remove(doc) {
  if (doc.can_delete !== true) return;
  if (
    !window.confirm(
      `¿Eliminar «${docName(doc)}»? Esta acción no se puede deshacer.`,
    )
  )
    return;
  emit("delete", doc);
}

onBeforeUnmount(closePreview);
</script>
