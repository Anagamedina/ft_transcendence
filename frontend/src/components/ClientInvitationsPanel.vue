<!--
  CLIENT INVITATIONS PANEL
  "Invitaciones" block of the admin client detail, as in the client design: the
  pending invitations of one organization and the "Invitar" form, which creates
  an invitation (POST /api/invitations, B4) and shows the link to send.
  The person writes their name and password when accepting the link.
  Data: organizations store (fetchInvitations, createInvitation). Reloads the
  pending list when it is mounted, so an accepted invitation is gone when the tab opens again.
  Usage:
    <ClientInvitationsPanel :organization-id="client.id" />
-->

<template>
  <section
    class="rounded-xl border border-gray-200 bg-white p-5"
    aria-labelledby="client-invitations-title"
  >
    <header class="mb-2 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 id="client-invitations-title" class="font-bold text-gray-900">
          Invitaciones
          <span class="font-normal text-gray-600">({{ pendingText }})</span>
        </h2>
        <p class="text-sm text-gray-600">Accesos pendientes de aceptar.</p>
      </div>
      <button
        v-if="!formOpen"
        ref="openButton"
        type="button"
        :class="BUTTON_PRIMARY"
        @click="openForm"
      >
        Invitar
      </button>
    </header>

    <ul v-if="invitations.length > 0">
      <li
        v-for="invitation in invitations"
        :key="invitation.id"
        class="flex flex-wrap items-center justify-between gap-3 border-t border-gray-200 py-4 first:border-t-0"
      >
        <div class="min-w-0">
          <p class="break-all font-semibold text-gray-900">
            {{ invitation.email }}
          </p>
          <p class="text-sm text-gray-600">
            Caduca el {{ formatDate(invitation.expires_at) }} · Sin aceptar
          </p>
        </div>
        <span
          class="whitespace-nowrap rounded-md bg-warning-light px-2 py-0.5 text-xs font-semibold text-warning-dark"
        >
          Pendiente
        </span>
      </li>
    </ul>
    <p v-else class="text-sm text-gray-600">No hay invitaciones pendientes.</p>

    <!-- New invitation -->
    <div v-if="formOpen" class="mt-4 space-y-3 rounded-lg bg-gray-50 p-4">
      <h3 class="font-semibold text-gray-900">Nueva invitación</h3>
      <form
        novalidate
        class="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end"
        @submit.prevent="onInvite"
        @keydown.esc="closeForm"
      >
        <div class="flex flex-col gap-1">
          <label for="invite-email" class="text-sm font-semibold text-gray-700">
            Email de la persona invitada <span aria-hidden="true">*</span>
          </label>
          <input
            id="invite-email"
            ref="emailInput"
            v-model="email"
            type="email"
            :maxlength="FIELD_LIMITS.email"
            required
            autocomplete="email"
            placeholder="persona@empresa.com"
            :class="INPUT"
            :aria-invalid="Boolean(error)"
            :aria-describedby="
              error
                ? 'invite-email-hint invite-email-error'
                : 'invite-email-hint'
            "
          />
        </div>
        <button
          type="submit"
          :class="BUTTON_PRIMARY"
          :disabled="inviting"
          :aria-busy="inviting"
        >
          {{ inviting ? "Creando…" : "Crear invitación" }}
        </button>
        <p id="invite-email-hint" class="text-xs text-gray-600 sm:col-span-2">
          Acceso de cliente a esta organización. La persona creará su cuenta al
          aceptar.
        </p>
        <p
          v-if="error"
          id="invite-email-error"
          role="alert"
          class="text-sm text-red-700 sm:col-span-2"
        >
          {{ error }}
        </p>
      </form>
      <button type="button" :class="TEXT_BUTTON" @click="closeForm">
        Cancelar
      </button>
    </div>

    <!-- The link is only available right after creating it (InvitationSentResponse) -->
    <div
      v-if="lastInvitation"
      class="mt-4 space-y-2 border-t border-gray-200 pt-4"
    >
      <p class="text-sm text-gray-700" role="status">
        Envía este enlace a {{ lastInvitation.email }} para que active su
        cuenta.
      </p>
      <InviteLinkCopy
        :link="lastInvitation.url"
        :expires-at="lastInvitation.expires_at"
      />
    </div>
  </section>
</template>

<script setup>
import { ref, computed, nextTick, watch } from "vue";
import InviteLinkCopy from "./InviteLinkCopy.vue";
import { useOrganizationsStore } from "../stores/organizations";
import { formatDate } from "../composables/useFormat";
import { apiErrorMessage } from "../utils/apiError";
import { FIELD_LIMITS } from "../utils/limits.js";

const props = defineProps({
  // Organization the invitations belong to
  organizationId: { type: String, required: true },
});

const organizationsStore = useOrganizationsStore();

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const BUTTON_PRIMARY =
  "min-h-10 rounded-lg border border-aqua-600 bg-aqua-600 px-4 text-sm font-semibold text-white hover:bg-aqua-700 disabled:cursor-wait disabled:opacity-60";
const TEXT_BUTTON =
  "min-h-10 px-1 text-sm font-semibold text-aqua-700 hover:underline";
const INPUT =
  "w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-aqua-600";

// The store keeps the pending invitations of the open client
const invitations = computed(() => organizationsStore.invitations);
const pendingText = computed(() =>
  invitations.value.length === 1
    ? "1 pendiente"
    : `${invitations.value.length} pendientes`,
);

const formOpen = ref(false);
const email = ref("");
const error = ref("");
const inviting = ref(false);
// InvitationSentResponse: the only answer with the link (url)
const lastInvitation = ref(null);
const emailInput = ref(null);
const openButton = ref(null);

function openForm() {
  formOpen.value = true;
  error.value = "";
  nextTick(() => emailInput.value?.focus());
}

function closeForm() {
  formOpen.value = false;
  email.value = "";
  error.value = "";
  nextTick(() => openButton.value?.focus());
}

async function onInvite() {
  const value = email.value.trim();
  if (!EMAIL_PATTERN.test(value)) {
    error.value = "Escribe un email válido, por ejemplo nombre@empresa.com.";
    emailInput.value?.focus();
    return;
  }
  error.value = "";
  inviting.value = true;
  try {
    // The store also adds it to the pending list
    lastInvitation.value = await organizationsStore.createInvitation({
      email: value,
      organization_id: props.organizationId,
    });
    email.value = "";
    formOpen.value = false;
    nextTick(() => openButton.value?.focus());
  } catch (err) {
    error.value = apiErrorMessage(
      err,
      "No se ha podido crear la invitación. Inténtalo de nuevo.",
    );
    emailInput.value?.focus();
  } finally {
    inviting.value = false;
  }
}

// On open, and again if the page moves to another client
watch(
  () => props.organizationId,
  (id) => {
    formOpen.value = false;
    lastInvitation.value = null;
    organizationsStore.fetchInvitations(id);
  },
  { immediate: true },
);
</script>
