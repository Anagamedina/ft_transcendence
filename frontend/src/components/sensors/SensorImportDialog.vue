<!--
  SENSOR IMPORT DIALOG
  Imports the sensors of a building from a CSV (POST /api/sensors/import).
  Three steps: choose the building and the file; check it (dry_run) and see
  the preview or every error with its line; confirm. All or nothing: if a
  line fails, the API creates none. Emits "imported" with how many it made.
-->

<template>
  <Modal
    :show="show"
    title="Importar sensores desde un CSV"
    size="lg"
    @close="close"
  >
    <!-- Done -->
    <div v-if="created !== null" class="space-y-3" role="status">
      <p class="font-semibold text-success-dark">
        ✓ {{ sensorsText(created) }}
        {{ created === 1 ? "creado" : "creados" }} en {{ preview.site_name }}.
      </p>
    </div>

    <form
      v-else
      id="sensor-import-form"
      novalidate
      class="space-y-4"
      @submit.prevent="submit"
    >
      <p class="text-sm text-slate-600">
        Una fila por sensor. Columnas obligatorias:
        <code>external_id</code>, <code>name</code>, <code>min_pressure</code> y
        <code>max_pressure</code>; opcionales: <code>location</code> y
        <code>floor</code> (0 si falta). Si una fila tiene un error no se
        importa ninguna.
        <button
          type="button"
          class="font-semibold text-aqua-700 underline hover:text-aqua-900"
          @click="downloadTemplate"
        >
          Descargar plantilla
        </button>
      </p>

      <label class="block text-sm font-medium text-slate-700">
        Edificio
        <select
          v-model="siteId"
          required
          :disabled="busy"
          :class="[INPUT_CLASS, INPUT_SIZE.md, INPUT_OK_CLASS, 'mt-1 block']"
          @change="resetCheck"
        >
          <option value="" disabled>Elige un edificio</option>
          <option v-for="site in sortedSites" :key="site.id" :value="site.id">
            {{ site.organization_name }} · {{ site.name }}
          </option>
        </select>
      </label>

      <label class="block text-sm font-medium text-slate-700">
        Archivo CSV
        <input
          ref="fileInput"
          type="file"
          accept=".csv,text/csv"
          required
          :disabled="busy"
          class="mt-1 block w-full text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-aqua-50 file:px-3 file:py-2 file:font-semibold file:text-aqua-700"
          @change="selectFile"
        />
      </label>

      <FormError :message="error" />

      <!-- Errors by line: everything the file has to fix, at once -->
      <div v-if="rowErrors.length" role="alert" class="space-y-2">
        <p class="text-sm font-semibold text-danger-dark">{{ rowErrorsTitle }}</p>
        <div class="max-h-64 overflow-auto rounded-lg border border-danger/40">
          <table class="w-full text-sm">
            <caption class="sr-only">
              Errores del archivo
            </caption>
            <thead class="sticky top-0 bg-danger-light text-left text-slate-700">
              <tr>
                <th scope="col" class="px-3 py-2">Línea</th>
                <th scope="col" class="px-3 py-2">Columna</th>
                <th scope="col" class="px-3 py-2">Error</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(item, index) in rowErrors"
                :key="index"
                class="border-t border-danger/40"
              >
                <td class="px-3 py-1.5 tabular-nums">{{ item.row }}</td>
                <td class="px-3 py-1.5">
                  <code>{{ item.field }}</code>
                </td>
                <td class="px-3 py-1.5">{{ item.message }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Preview: what will be created -->
      <div v-if="preview" class="space-y-2">
        <p class="text-sm font-semibold text-slate-800">
          Se {{ preview.sensors.length === 1 ? "creará" : "crearán" }}
          {{ sensorsText(preview.sensors.length) }} en {{ preview.site_name }}:
        </p>
        <div class="max-h-64 overflow-auto rounded-lg border border-slate-200">
          <table class="w-full text-sm">
            <caption class="sr-only">
              Sensores que se van a crear
            </caption>
            <thead class="sticky top-0 bg-slate-50 text-left text-slate-600">
              <tr>
                <th scope="col" class="px-3 py-2">Etiqueta</th>
                <th scope="col" class="px-3 py-2">Nombre</th>
                <th scope="col" class="px-3 py-2 text-right">Planta</th>
                <th scope="col" class="px-3 py-2 text-right">Umbrales (bar)</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="sensor in preview.sensors"
                :key="sensor.external_id"
                class="border-t border-slate-100"
              >
                <td class="px-3 py-1.5">{{ sensor.external_id }}</td>
                <td class="px-3 py-1.5">
                  {{ sensor.name }}
                  <span v-if="sensor.location" class="text-slate-500">
                    · {{ sensor.location }}</span
                  >
                </td>
                <td class="px-3 py-1.5 text-right tabular-nums">
                  {{ sensor.floor }}
                </td>
                <td class="px-3 py-1.5 text-right tabular-nums">
                  {{ bar(sensor.min_pressure) }} –
                  {{ bar(sensor.max_pressure) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </form>

    <template #footer>
      <button
        type="button"
        class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:border-aqua-600"
        @click="close"
      >
        {{ created !== null ? "Cerrar" : "Cancelar" }}
      </button>
      <button
        v-if="created === null"
        type="submit"
        form="sensor-import-form"
        :disabled="busy || !siteId || !file"
        class="rounded-lg bg-aqua-600 px-4 py-2 text-sm font-semibold text-white hover:bg-aqua-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {{ submitLabel }}
      </button>
    </template>
  </Modal>
</template>

<script setup>
import { computed, ref } from "vue";
import Modal from "../Modal.vue";
import FormError from "../FormError.vue";
import { INPUT_CLASS, INPUT_OK_CLASS, INPUT_SIZE } from "../../composables/useFieldErrors.js";
import sensorsService from "../../services/sensors.service.js";
import { apiErrorMessage } from "../../utils/apiError";
import { saveBlob } from "../../utils/download.js";

const props = defineProps({
  show: { type: Boolean, default: false },
  // Buildings the admin can choose: { id, name, organization_name }
  sites: { type: Array, default: () => [] },
});

const emit = defineEmits(["close", "imported"]);

// Same limit as the gateway and the API (MAX_UPLOAD_MB)
const MAX_SIZE = 10 * 1024 * 1024;

// The template opens well in Excel in Spanish: ";" and decimal comma, with
// a BOM so the accents are read as UTF-8
const TEMPLATE =
  "external_id;name;location;floor;min_pressure;max_pressure\r\n" +
  "T-101;Cocina;Planta 1 - Cocina;1;1,5;6\r\n" +
  "T-102;Sala de bombas;Sótano;-1;2;7,5\r\n";

const siteId = ref("");
const file = ref(null);
const fileInput = ref(null);
const busy = ref(false);
const error = ref("");
const rowErrors = ref([]);
// Result of the dry run: what will be created. Confirming sends the same file
const preview = ref(null);
// How many were created; null until the import is confirmed
const created = ref(null);

const sortedSites = computed(() =>
  [...props.sites].sort((a, b) =>
    `${a.organization_name} ${a.name}`.localeCompare(
      `${b.organization_name} ${b.name}`,
      "es",
    ),
  ),
);

const submitLabel = computed(() => {
  if (busy.value) return preview.value ? "Importando…" : "Comprobando…";
  return preview.value
    ? `Importar ${sensorsText(preview.value.sensors.length)}`
    : "Comprobar archivo";
});

const rowErrorsTitle = computed(() => {
  const lines = new Set(rowErrors.value.map((item) => item.row)).size;
  return `${lines} ${lines === 1 ? "línea tiene" : "líneas tienen"} errores. Corrige el archivo y vuelve a elegirlo: no se ha importado nada.`;
});

function sensorsText(count) {
  return `${count} ${count === 1 ? "sensor" : "sensores"}`;
}

function bar(value) {
  return new Intl.NumberFormat("es-ES", { maximumFractionDigits: 2 }).format(
    value,
  );
}

// A new building or file has to be checked again before importing
function resetCheck() {
  error.value = "";
  rowErrors.value = [];
  preview.value = null;
}

function selectFile(event) {
  resetCheck();
  const selected = event.target.files?.[0] ?? null;
  file.value = null;
  if (!selected) return;
  if (!selected.name.toLowerCase().endsWith(".csv")) {
    error.value = "Elige un archivo .csv.";
  } else if (selected.size === 0) {
    error.value = "El archivo está vacío.";
  } else if (selected.size > MAX_SIZE) {
    error.value = "El archivo supera el límite de 10 MB.";
  } else {
    file.value = selected;
  }
}

// First click: dry run (preview or errors). Second: the real import
async function submit() {
  if (!siteId.value || !file.value) return;
  const dryRun = !preview.value;
  busy.value = true;
  error.value = "";
  rowErrors.value = [];
  try {
    const response = await sensorsService.importSensors({
      file: file.value,
      site_id: siteId.value,
      dry_run: dryRun,
    });
    if (dryRun) {
      preview.value = response.data;
    } else {
      created.value = response.data.created;
      emit("imported", response.data.created);
    }
  } catch (err) {
    preview.value = null;
    if (err?.code === "IMPORT_INVALID_ROWS" && Array.isArray(err.details)) {
      rowErrors.value = err.details;
    } else {
      error.value = apiErrorMessage(
        err,
        "No se ha podido importar el archivo.",
      );
    }
  } finally {
    busy.value = false;
  }
}

function downloadTemplate() {
  const blob = new Blob(["\ufeff" + TEMPLATE], {
    type: "text/csv;charset=utf-8",
  });
  saveBlob(blob, "plantilla-sensores.csv");
}

function close() {
  siteId.value = "";
  file.value = null;
  if (fileInput.value) fileInput.value.value = "";
  resetCheck();
  created.value = null;
  emit("close");
}
</script>
