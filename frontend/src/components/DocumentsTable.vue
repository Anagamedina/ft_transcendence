<!--Component used for Documentsview-->

<template>
  <section class="space-y-4">
    <div class="flex flex-wrap gap-3">
      <label class="text-sm text-slate-700">
        Edificio
        <select
          v-model="siteId"
          class="ml-2 rounded-md border border-slate-300 bg-white px-3 py-2"
          @change="emitFilters"
        >
          <option value="">Todos los edificios</option>
          <option v-for="site in sites" :key="site.id" :value="site.id">
            {{ site.name }}
          </option>
        </select>
      </label>

      <label class="text-sm text-slate-700">
        Tipo
        <select
          v-model="kind"
          class="ml-2 rounded-md border border-slate-300 bg-white px-3 py-2"
          @change="emitFilters"
        >
          <option value="">Todos los tipos</option>
          <option value="PLAN">Plan</option>
          <option value="REPORT">Informe</option>
          <option value="INVOICE">Factura</option>
          <option value="PHOTO">Foto</option>
          <option value="OTHER">Otro</option>
        </select>
      </label>
    </div>

    <div class="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50 text-left text-xs uppercase text-slate-500">
          <tr>
            <th class="px-4 py-3">Documento</th>
            <th class="px-4 py-3">Tipo</th>
            <th class="px-4 py-3">Edificio</th>
            <th class="px-4 py-3">Fecha</th>
            <th class="px-4 py-3">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="doc in documents" :key="doc.id">
            <td class="px-4 py-3 font-medium text-slate-800">
              {{ doc.filename || doc.name || `Documento ${doc.id}` }}
            </td>
            <td class="px-4 py-3 text-slate-600">
              {{ kindLabel(doc.kind) }}
            </td>
            <td class="px-4 py-3 text-slate-600">
              {{ doc.site_name || doc.site_id || "—" }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-slate-600">
              {{ formatDate(doc.created_at) }}
            </td>
            <td class="px-4 py-3">
              <div class="flex flex-wrap gap-3">
                <button
                  type="button"
                  class="text-blue-700 hover:underline"
                  :disabled="busyId === doc.id"
                  @click="download(doc)"
                >
                  Descargar
                </button>

                <button
                  v-if="isPreviewable(doc)"
                  type="button"
                  class="text-blue-700 hover:underline"
                  :disabled="busyId === doc.id"
                  @click="preview(doc)"
                >
                  Vista previa
                </button>

                <button
                  v-if="doc.can_delete === true"
                  type="button"
                  class="text-red-600 hover:underline"
                  :disabled="busyId === doc.id"
                  @click="remove(doc)"
                >
                  Eliminar
                </button>
              </div>
            </td>
          </tr>

          <tr v-if="documents.length === 0">
            <td colspan="5" class="px-4 py-8 text-center text-slate-500">
              No hay documentos para estos filtros.
            </td>
          </tr>
        </tbody>
      </table>

      <div
        v-if="pages > 1"
        class="flex items-center justify-between border-t border-slate-200 px-4 py-3"
      >
        <button
          type="button"
          class="rounded-md border border-slate-300 px-3 py-2 disabled:opacity-40"
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
          class="rounded-md border border-slate-300 px-3 py-2 disabled:opacity-40"
          :disabled="page >= pages"
          @click="$emit('page-change', page + 1)"
        >
          Siguiente
        </button>
      </div>
    </div>

    <div
      v-if="previewUrl"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      @click.self="closePreview"
    >
      <div class="max-h-[90vh] w-full max-w-4xl overflow-auto rounded-xl bg-white p-4">
        <div class="mb-3 flex items-center justify-between gap-3">
          <h3 class="truncate font-semibold">{{ previewName }}</h3>
          <button
            type="button"
            class="rounded-md border px-3 py-1.5 text-sm"
            @click="closePreview"
          >
            Cerrar
          </button>
        </div>

        <img
          v-if="previewType.startsWith('image/')"
          :src="previewUrl"
          :alt="previewName"
          class="mx-auto max-h-[75vh] max-w-full object-contain"
        />
        <iframe
          v-else-if="previewType === 'application/pdf'"
          :src="previewUrl"
          :title="previewName"
          class="h-[75vh] w-full"
        />
      </div>
    </div>

    <p v-if="actionError" role="alert" class="text-sm text-red-600">
      {{ actionError }}
    </p>
  </section>
</template>

<script setup>
import { onBeforeUnmount, ref } from "vue";
import { useDocumentsStore } from "../stores/documents";

defineProps({
  documents: { type: Array, default: () => [] },
  sites: { type: Array, default: () => [] },
  page: { type: Number, default: 1 },
  pages: { type: Number, default: 0 },
});

const emit = defineEmits(["filters-change", "page-change", "delete"]);
const documentsStore = useDocumentsStore();

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
  return ({
    PLAN: "Plan",
    REPORT: "Informe",
    INVOICE: "Factura",
    PHOTO: "Foto",
    OTHER: "Otro",
  })[value] || value || "—";
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("es-ES", { dateStyle: "medium" }).format(date);
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
    previewName.value = doc.filename || "Vista previa";
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
  if (!window.confirm(`¿Eliminar "${doc.filename}"? Esta acción no se puede deshacer.`)) return;
  emit("delete", doc);
}

onBeforeUnmount(closePreview);
</script>
