<!--
  FILE DROPZONE
  Upload form of a document: building, type and file (PDF, JPG, PNG or CSV,
  10 MB max). Shown inside the "Subir documento" modal of DocumentsView (F27).
  Emits "upload" with { file, site_id, kind } and "cancel" to close the modal.
  Usage:
    <FileDropzone :sites="sites" :uploading="uploading" :progress="progress"
      @upload="handleUpload" @cancel="close" />
-->

<template>
  <form class="space-y-4" @submit.prevent="submit">
    <p class="text-sm text-slate-600">
      PDF, JPG, PNG o CSV. Tamaño máximo: 10 MB.
    </p>

    <div class="grid gap-4 sm:grid-cols-2">
      <label class="block text-sm font-medium text-slate-700">
        Edificio
        <select
          v-model="siteId"
          required
          class="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2"
        >
          <option value="" disabled>Selecciona un edificio</option>
          <option v-for="site in sites" :key="site.id" :value="site.id">
            {{ site.name }}
          </option>
        </select>
      </label>

      <label class="block text-sm font-medium text-slate-700">
        Tipo de documento
        <select
          v-model="kind"
          required
          class="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2"
        >
          <option value="PLAN">Plano</option>
          <option value="REPORT">Informe</option>
          <option value="INVOICE">Factura</option>
          <option value="PHOTO">Foto</option>
          <option value="OTHER">Otro</option>
        </select>
      </label>
    </div>

    <!-- The whole box opens the file picker; the input stays reachable by keyboard -->
    <label
      class="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-300 px-5 py-8 text-center hover:border-aqua-400 hover:bg-aqua-50 focus-within:border-aqua-600 focus-within:ring-2 focus-within:ring-aqua-400"
    >
      <span class="text-sm font-semibold text-slate-800">
        Selecciona un archivo
      </span>
      <span class="mt-1 text-xs text-slate-600">
        PDF, JPG, PNG o CSV · 10 MB máximo
      </span>
      <input
        class="sr-only"
        type="file"
        accept=".pdf,.jpg,.jpeg,.png,.csv,application/pdf,image/jpeg,image/png,text/csv"
        :disabled="uploading"
        @change="selectFile"
      />
    </label>

    <div v-if="file" class="flex items-center justify-between gap-3 text-sm">
      <div class="min-w-0">
        <p class="truncate font-medium text-slate-800">{{ file.name }}</p>
        <p class="text-slate-600">{{ formatSize(file.size) }}</p>
      </div>
      <button
        v-if="!uploading"
        type="button"
        class="shrink-0 text-sm font-semibold text-danger-dark hover:underline"
        @click="clearFile"
      >
        Quitar
      </button>
    </div>

    <p v-if="error" role="alert" class="text-sm text-danger-dark">
      {{ error }}
    </p>

    <div v-if="uploading" class="space-y-1">
      <div class="flex justify-between text-xs text-slate-600">
        <span>Subiendo archivo…</span>
        <span>{{ progress }}%</span>
      </div>
      <div
        class="h-2 overflow-hidden rounded-full bg-slate-200"
        role="progressbar"
        aria-label="Progreso de subida"
        :aria-valuenow="progress"
        aria-valuemin="0"
        aria-valuemax="100"
      >
        <div
          class="h-full rounded-full bg-aqua-600 transition-all"
          :style="{ width: `${progress}%` }"
        />
      </div>
    </div>

    <p v-if="sites.length === 0" class="text-sm text-slate-600">
      Necesitas al menos un edificio para subir documentos.
    </p>

    <div class="flex flex-wrap justify-end gap-3">
      <button
        type="button"
        :disabled="uploading"
        class="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
        @click="$emit('cancel')"
      >
        Cancelar
      </button>
      <button
        type="submit"
        :disabled="!file || !siteId || uploading || sites.length === 0"
        class="rounded-lg bg-aqua-600 px-4 py-2 text-sm font-semibold text-white hover:bg-aqua-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {{ uploading ? "Subiendo…" : "Subir" }}
      </button>
    </div>
  </form>
</template>

<script setup>
import { ref } from "vue";

const props = defineProps({
  sites: { type: Array, default: () => [] },
  uploading: { type: Boolean, default: false },
  progress: { type: Number, default: 0 },
});

const emit = defineEmits(["upload", "cancel"]);

const MAX_SIZE = 10 * 1024 * 1024;
const ALLOWED_EXTENSIONS = ["pdf", "jpg", "jpeg", "png", "csv"];

const file = ref(null);
// With only one building it is selected already
const siteId = ref(props.sites.length === 1 ? props.sites[0].id : "");
const kind = ref("OTHER");
const error = ref("");

function selectFile(event) {
  error.value = "";
  const selected = event.target.files?.[0];

  if (!selected) return;

  const extension = selected.name.split(".").pop()?.toLowerCase();

  if (!ALLOWED_EXTENSIONS.includes(extension)) {
    file.value = null;
    error.value = "Formato no admitido. Usa PDF, JPG, PNG o CSV.";
  } else if (selected.size === 0) {
    file.value = null;
    error.value = "El archivo está vacío.";
  } else if (selected.size > MAX_SIZE) {
    file.value = null;
    error.value = "El archivo supera el límite de 10 MB.";
  } else {
    file.value = selected;
  }

  // Lets the same file be chosen again after "Quitar"
  event.target.value = "";
}

function clearFile() {
  file.value = null;
  error.value = "";
}

function submit() {
  if (!file.value || !siteId.value || props.uploading) return;
  error.value = "";
  emit("upload", {
    file: file.value,
    site_id: siteId.value,
    kind: kind.value,
  });
}

function formatSize(size) {
  return size < 1024 * 1024
    ? `${(size / 1024).toFixed(0)} KB`
    : `${(size / (1024 * 1024)).toFixed(2)} MB`;
}
</script>
