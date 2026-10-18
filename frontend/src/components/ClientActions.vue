<!--
  CLIENT ACTIONS
  "Acciones" tab of the client detail: status changes (B1) and delete (B16).
  Shows only the actions that make sense for the client's status.
  Destructive actions (suspend, delete) ask for confirmation on the page itself, no popup.
  Presentational: emits the chosen action; the parent calls the API and updates the client.
  Usage:
    <ClientActions :client="client" @extend="..." @activate="..." @suspend="..." @reactivate="..." @delete="..." />
-->

<template>
  <div class="space-y-4">
    <!-- Status card: trial, active or suspended -->
    <section
      class="space-y-3 rounded-xl border border-gray-200 bg-white p-5"
      aria-labelledby="actions-status-title"
    >
      <h2 id="actions-status-title" class="text-lg font-bold text-gray-900">
        {{ statusTitle }}
      </h2>
      <p class="text-gray-600">{{ statusText }}</p>

      <div class="flex flex-wrap gap-2">
        <template v-if="client.status === 'TRIAL'">
          <button
            type="button"
            :class="BUTTON_OUTLINE"
            @click="$emit('extend')"
          >
            Ampliar prueba 7 días
          </button>
          <button
            type="button"
            :class="BUTTON_PRIMARY"
            @click="$emit('activate')"
          >
            Activar como cliente
          </button>
        </template>
        <button
          v-if="client.status !== 'SUSPENDED'"
          ref="suspendButton"
          type="button"
          :class="BUTTON_WARNING"
          :aria-expanded="confirming === 'suspend'"
          @click="ask('suspend')"
        >
          Suspender
        </button>
        <button
          v-else
          type="button"
          :class="BUTTON_PRIMARY"
          @click="$emit('reactivate')"
        >
          Reactivar
        </button>
      </div>

      <!-- Inline confirmation for suspend -->
      <div
        v-if="confirming === 'suspend'"
        role="alertdialog"
        aria-labelledby="confirm-suspend-text"
        @keydown.esc="cancel"
        class="flex flex-col gap-3 rounded-lg border border-amber-300 bg-amber-50 p-4 sm:flex-row sm:items-center sm:justify-between"
      >
        <p id="confirm-suspend-text" class="text-amber-900">
          <strong>¿Suspender {{ client.name }}?</strong>
          {{ suspendText }}
        </p>
        <div class="flex shrink-0 gap-2">
          <button
            ref="cancelButton"
            type="button"
            :class="BUTTON_SECONDARY"
            @click="cancel"
          >
            Cancelar
          </button>
          <button
            type="button"
            :class="BUTTON_WARNING_SOLID"
            @click="confirm('suspend')"
          >
            Sí, suspender
          </button>
        </div>
      </div>
    </section>

    <!-- Danger zone: delete -->
    <section
      class="space-y-3 rounded-xl border border-red-200 bg-white p-5"
      aria-labelledby="actions-delete-title"
    >
      <div
        class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <h2 id="actions-delete-title" class="text-lg font-bold text-red-800">
            Eliminar cliente
          </h2>
          <p class="text-sm text-gray-600">
            Borra la organización, sus edificios, sensores y lecturas. No se
            puede deshacer.
          </p>
        </div>
        <button
          ref="deleteButton"
          type="button"
          :class="BUTTON_DANGER"
          :aria-expanded="confirming === 'delete'"
          @click="ask('delete')"
        >
          Eliminar…
        </button>
      </div>

      <!-- Inline confirmation for delete -->
      <div
        v-if="confirming === 'delete'"
        role="alertdialog"
        aria-labelledby="confirm-delete-text"
        @keydown.esc="cancel"
        class="flex flex-col gap-3 rounded-lg border border-red-300 bg-red-50 p-4 sm:flex-row sm:items-center sm:justify-between"
      >
        <p id="confirm-delete-text" class="text-red-900">
          <strong>¿Eliminar {{ client.name }} para siempre?</strong>
          {{ deleteText }}
        </p>
        <div class="flex shrink-0 gap-2">
          <button
            ref="cancelButton"
            type="button"
            :class="BUTTON_SECONDARY"
            @click="cancel"
          >
            Cancelar
          </button>
          <button
            type="button"
            :class="BUTTON_DANGER"
            @click="confirm('delete')"
          >
            Sí, eliminar
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from "vue";
import { useClientStatus } from "../composables/useClientStatus";
import { useFormat } from "../composables/useFormat";

const props = defineProps({
  // OrganizationResponse: uses name, status, trial_ends_at, user_count and site_count
  client: { type: Object, required: true },
});

const emit = defineEmits([
  "extend",
  "activate",
  "suspend",
  "reactivate",
  "delete",
]);

const BASE = "min-h-10 rounded-lg border px-4 text-sm font-semibold";
const BUTTON_PRIMARY = `${BASE} border-aqua-600 bg-aqua-600 text-white hover:bg-aqua-700`;
const BUTTON_OUTLINE = `${BASE} border-aqua-600 bg-white text-aqua-600 hover:bg-aqua-50`;
const BUTTON_SECONDARY = `${BASE} border-gray-300 bg-white text-gray-700 hover:border-aqua-600`;
const BUTTON_WARNING = `${BASE} border-amber-600 bg-white text-amber-800 hover:bg-amber-50`;
const BUTTON_WARNING_SOLID = `${BASE} border-amber-700 bg-amber-700 text-white hover:bg-amber-800`;
const BUTTON_DANGER = `${BASE} border-red-700 bg-red-700 text-white hover:bg-red-800`;

// Which confirmation is open: 'suspend', 'delete' or null
const confirming = ref(null);

const suspendButton = ref(null);
const deleteButton = ref(null);
const cancelButton = ref(null);

// '21 oct 2026'
const { formatDate } = useFormat();

const status = computed(() => useClientStatus(props.client));

const statusTitle = computed(() => {
  if (props.client.status === "TRIAL") return "Prueba gratuita";
  if (props.client.status === "SUSPENDED") return "Cliente suspendido";
  return "Cliente activo";
});

const statusText = computed(() => {
  if (props.client.status === "SUSPENDED")
    return "Sus usuarios no pueden entrar hasta que lo reactives.";
  if (props.client.status === "ACTIVE")
    return "El cliente tiene acceso completo.";
  const end = formatDate(props.client.trial_ends_at);
  return status.value.trialEnded
    ? `Terminó el ${end}. El cliente está en solo lectura.`
    : `Termina el ${end}. Al terminar, el cliente queda en solo lectura.`;
});

// Singular and plural sentences, so the confirmation always reads naturally
const suspendText = computed(() => {
  const users = props.client.user_count;
  if (users === 0) return "No podrá usar AquaGuard hasta que lo reactives.";
  if (users === 1) return "Su usuario no podrá entrar hasta que lo reactives.";
  return `Sus ${users} usuarios no podrán entrar hasta que lo reactives.`;
});

const deleteText = computed(() => {
  const sites = props.client.site_count;
  if (sites === 0) return "Se borrarán todos sus datos.";
  if (sites === 1)
    return "Se borrarán su edificio, sus sensores y todo su histórico.";
  return `Se borrarán sus ${sites} edificios, sus sensores y todo su histórico.`;
});

// Opens a confirmation (Escape closes it, like Cancelar) and moves the focus to "Cancelar", the safe choice
function ask(action) {
  confirming.value = action;
  nextTick(() => cancelButton.value?.focus());
}

// Closes the confirmation and gives the focus back to the button that opened it
function cancel() {
  const opener = confirming.value === "delete" ? deleteButton : suspendButton;
  confirming.value = null;
  nextTick(() => opener.value?.focus());
}

function confirm(action) {
  confirming.value = null;
  emit(action);
}
</script>
