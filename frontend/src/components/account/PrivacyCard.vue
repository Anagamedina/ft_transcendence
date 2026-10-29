<template>
  <section
    class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
    aria-labelledby="privacy-title"
  >
    <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
      <h2 id="privacy-title" class="text-lg font-bold text-slate-800">
        Privacidad
      </h2>
      <!-- Text pill, not only color: the state is readable without seeing it -->
      <span
        v-if="authStore.deletionRequestedAt"
        class="rounded-full bg-warning-light px-3 py-0.5 text-xs font-semibold text-warning-dark"
        >Baja solicitada</span
      >
    </div>

    <!-- Export my data -->
    <div class="space-y-3">
      <p class="text-sm text-slate-700">
        Descarga una copia de tu cuenta, tu organización y tus edificios en
        formato JSON. Te enviaremos un email de confirmación a
        <strong class="font-semibold">{{ accountEmail }}</strong
        >.
      </p>
      <p v-if="exportError" class="text-sm text-danger-dark" role="alert">
        {{ exportError }}
      </p>
      <button
        type="button"
        :disabled="exporting"
        class="rounded-lg border border-aqua-600 bg-white px-4 py-2 font-semibold text-aqua-700 hover:bg-aqua-50 disabled:opacity-50"
        @click="downloadMyData"
      >
        {{ exporting ? "Preparando…" : "Descargar mis datos" }}
      </button>
    </div>

    <hr class="my-5 border-slate-200" />

    <!-- Deletion request -->
    <div class="space-y-3">
      <!-- Already requested: show the date, no button -->
      <p
        v-if="authStore.deletionRequestedAt"
        role="status"
        class="rounded-lg border border-warning-light bg-warning-light px-3 py-2 text-sm text-warning-dark"
      >
        Pediste la baja el {{ formatDate(authStore.deletionRequestedAt) }}. Un
        administrador la tramitará; hasta entonces puedes seguir entrando y
        descargar tus datos.
      </p>

      <template v-else>
        <p class="text-sm text-slate-700">
          Si pides la baja, un administrador revisará la petición y cerrará tu
          cuenta. Hasta entonces puedes seguir entrando y descargar tus datos.
          Recibirás un email de confirmación cuando la pidas.
        </p>

        <!-- Confirmation on the page itself, no browser dialog -->
        <div
          v-if="confirming"
          class="space-y-3 rounded-lg border border-danger-light bg-danger-light p-4"
          role="group"
          aria-labelledby="deletion-confirm-text"
        >
          <p
            id="deletion-confirm-text"
            class="text-sm font-medium text-danger-dark"
          >
            ¿Seguro que quieres pedir la baja? No se borra nada todavía: un
            administrador revisará la petición.
          </p>
          <p v-if="deletionError" class="text-sm text-danger-dark" role="alert">
            {{ deletionError }}
          </p>
          <div class="flex flex-wrap gap-3">
            <button
              ref="confirmButton"
              type="button"
              :disabled="requesting"
              class="rounded-lg bg-danger-dark px-4 py-2 font-semibold text-white hover:opacity-90 disabled:opacity-50"
              @click="confirmDeletion"
            >
              {{ requesting ? "Enviando…" : "Sí, pedir la baja" }}
            </button>
            <button
              type="button"
              :disabled="requesting"
              class="rounded-lg border border-slate-300 bg-white px-4 py-2 font-semibold text-slate-700 hover:bg-slate-50"
              @click="cancelDeletion"
            >
              Cancelar
            </button>
          </div>
        </div>

        <button
          v-else
          ref="requestButton"
          type="button"
          class="rounded-lg border border-danger-light bg-white px-4 py-2 font-semibold text-danger-dark hover:bg-danger-light"
          @click="startDeletion"
        >
          Pedir la baja
        </button>
      </template>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, nextTick } from "vue";
import { useAuthStore } from "../../stores/auth";
import { formatDate } from "../../composables/useFormat";
import { apiErrorMessage } from "../../utils/apiError";
import { saveBlob } from "../../utils/download.js";

const authStore = useAuthStore();

// Where the confirmation emails go (B19): the account address
const accountEmail = computed(() => authStore.user?.email ?? "");

const exporting = ref(false);
const exportError = ref("");
const confirming = ref(false);
const requesting = ref(false);
const deletionError = ref("");
const confirmButton = ref(null);
const requestButton = ref(null);

// Gets the JSON from the API and saves it as a file, with the backend's file name
async function downloadMyData() {
  exporting.value = true;
  exportError.value = "";
  try {
    const data = await authStore.exportMyData();
    const day = (data.exported_at ?? new Date().toISOString()).slice(0, 10);
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    saveBlob(blob, `aquaguard-mis-datos_${day}.json`);
  } catch (error) {
    exportError.value = apiErrorMessage(
      error,
      "No se han podido descargar tus datos.",
    );
  } finally {
    exporting.value = false;
  }
}

// Shows the confirmation and moves the focus to it (keyboard and screen readers)
async function startDeletion() {
  deletionError.value = "";
  confirming.value = true;
  await nextTick();
  confirmButton.value?.focus();
}

async function cancelDeletion() {
  confirming.value = false;
  await nextTick();
  requestButton.value?.focus();
}

async function confirmDeletion() {
  requesting.value = true;
  deletionError.value = "";
  try {
    await authStore.requestDeletion();
    confirming.value = false;
  } catch (error) {
    deletionError.value = apiErrorMessage(
      error,
      "No se ha podido registrar la petición de baja.",
    );
  } finally {
    requesting.value = false;
  }
}
</script>
