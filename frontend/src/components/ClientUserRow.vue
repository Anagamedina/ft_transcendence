<!--
  CLIENT USER ROW
  One user in the "Usuarios" tab of the admin client detail (F23), as in the
  client design: initials, name, email, role and state, with two actions:
    - Editar: the name inline (PATCH /api/users/{id}). The role is shown but
      not editable: a client user stays a client.
    - Quitar acceso: inline confirmation, same pattern as "Eliminar cliente" in
      ClientActions (DELETE /api/users/{id}).
  The API errors of these actions (409, 422) are shown under the row.
  The admin of the session gets no actions on their own row: the API rejects them (409).
  The parent removes the user (`remove` prop): once it is gone from the store this
  row unmounts, and Vue drops the events of an unmounted component.
  Usage:
    <ClientUserRow :user="user" :is-self="false" :remove="removeUser" @updated="..." />
-->

<template>
  <li class="border-t border-slate-200 py-4 first:border-t-0">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex min-w-0 flex-1 items-center gap-3">
        <UserAvatar :name="user.name" />
        <div class="min-w-0">
          <p class="font-semibold text-slate-900">
            {{ user.name }}
            <span v-if="isSelf" class="font-normal text-slate-600">(tú)</span>
          </p>
          <p class="break-all text-sm text-slate-600">{{ user.email }}</p>
          <p class="text-sm text-slate-600">
            Rol: {{ ROLE_LABELS[user.role] ?? user.role }} · Último acceso:
            {{ formatDateTime(user.last_login_at, { empty: "nunca" }) }}
          </p>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-3">
        <span
          class="whitespace-nowrap rounded-md px-2 py-0.5 text-xs font-semibold"
          :class="
            user.is_active
              ? 'bg-success-light text-success-dark'
              : 'bg-slate-100 text-slate-700'
          "
        >
          {{ user.is_active ? "Activo" : "Desactivado" }}
        </span>
        <template v-if="!isSelf && mode === 'view'">
          <button
            ref="editButton"
            type="button"
            :class="TEXT_BUTTON"
            :aria-label="`Editar a ${user.name}`"
            @click="openEdit"
          >
            Editar
          </button>
          <button
            ref="removeButton"
            type="button"
            :class="[TEXT_BUTTON, 'text-danger-dark']"
            :aria-label="`Quitar acceso a ${user.name}`"
            @click="askRemove"
          >
            Quitar acceso
          </button>
        </template>
      </div>
    </div>

    <!-- Editar: only the name, inline as in the design -->
    <form
      v-if="mode === 'edit'"
      novalidate
      class="mt-3 space-y-3 rounded-lg bg-slate-50 p-4"
      :aria-label="`Editar a ${user.name}`"
      @submit.prevent="saveEdit"
      @keydown.esc="closeEdit"
    >
      <div class="flex flex-col gap-1">
        <label :for="`user-name-${user.id}`" :class="LABEL">
          Nombre del usuario <span aria-hidden="true">*</span>
        </label>
        <input
          :id="`user-name-${user.id}`"
          ref="nameInput"
          v-model="form.name"
          type="text"
          required
          maxlength="120"
          autocomplete="off"
          :class="INPUT"
          :aria-invalid="Boolean(error)"
          :aria-describedby="error ? `user-error-${user.id}` : undefined"
        />
      </div>

      <p class="text-xs text-slate-600">
        El email y el rol no se pueden cambiar.
      </p>

      <div class="flex flex-wrap gap-2">
        <button
          type="submit"
          :class="BUTTON_PRIMARY"
          :disabled="saving"
          :aria-busy="saving"
        >
          {{ saving ? "Guardando…" : "Guardar cambios" }}
        </button>
        <button type="button" :class="BUTTON_SECONDARY" @click="closeEdit">
          Cancelar
        </button>
      </div>
    </form>

    <!-- Quitar acceso: inline confirmation, "Cancelar" gets the focus -->
    <div
      v-if="mode === 'confirm'"
      role="alertdialog"
      :aria-labelledby="`confirm-remove-${user.id}`"
      class="mt-3 flex flex-col gap-3 rounded-lg border border-danger/40 bg-danger-light p-4 sm:flex-row sm:items-center sm:justify-between"
      @keydown.esc="cancelRemove"
    >
      <p :id="`confirm-remove-${user.id}`" class="text-danger-dark">
        <strong>¿Quitar el acceso a {{ user.name }}?</strong>
        Dejará de poder entrar en AquaGuard. No se puede deshacer.
      </p>
      <div class="flex shrink-0 gap-2">
        <button
          ref="cancelButton"
          type="button"
          :class="BUTTON_SECONDARY"
          @click="cancelRemove"
        >
          Cancelar
        </button>
        <button
          type="button"
          :class="BUTTON_DANGER"
          :disabled="removing"
          :aria-busy="removing"
          @click="confirmRemove"
        >
          {{ removing ? "Quitando…" : "Sí, quitar acceso" }}
        </button>
      </div>
    </div>

    <!-- API error of the last action (e.g. 409 CANNOT_DELETE_SELF) -->
    <p
      v-if="error"
      :id="`user-error-${user.id}`"
      role="alert"
      class="mt-3 rounded-lg border border-danger/40 bg-danger-light px-4 py-2 text-sm font-semibold text-danger-dark"
    >
      {{ error }}
    </p>
  </li>
</template>

<script setup>
import { ref, reactive, nextTick } from "vue";
import UserAvatar from "./UserAvatar.vue";
import { useUsersStore } from "../stores/users";
import { formatDateTime } from "../composables/useFormat";
import { apiErrorMessage } from "../utils/apiError";

const props = defineProps({
  // UserAdminResponse (B6): id, name, email, role, is_active, last_login_at…
  user: { type: Object, required: true },
  // The admin of the session: no actions on their own row
  isSelf: { type: Boolean, default: false },
  // async (user) => void: removes the user (DELETE /api/users/{id}); throws the API error
  remove: { type: Function, required: true },
});

// updated(user) with the API answer
const emit = defineEmits(["updated"]);

const usersStore = useUsersStore();

const ROLE_LABELS = { client: "Cliente", admin: "Admin" };

// Our own text for the errors this row can get; anything else keeps the API message
const ERROR_TEXTS = {
  CANNOT_DELETE_SELF: "No puedes quitarte el acceso a ti mismo.",
  INVALID_NAME: "El nombre no puede estar vacío.",
  ORGANIZATION_REQUIRED: "Un cliente tiene que pertenecer a una organización.",
  USER_NOT_FOUND: "Este usuario ya no existe. Recarga la página.",
};

function errorText(err, fallback) {
  return ERROR_TEXTS[err?.code] ?? apiErrorMessage(err, fallback);
}

const BASE = "min-h-10 rounded-lg border px-4 text-sm font-semibold";
const BUTTON_PRIMARY = `${BASE} border-aqua-600 bg-aqua-600 text-white hover:bg-aqua-700 disabled:cursor-wait disabled:opacity-60`;
const BUTTON_SECONDARY = `${BASE} border-slate-300 bg-white text-slate-700 hover:border-aqua-600`;
const BUTTON_DANGER = `${BASE} border-danger-dark bg-danger-dark text-white hover:bg-danger-dark/90 disabled:cursor-wait disabled:opacity-60`;
const TEXT_BUTTON =
  "min-h-10 px-1 text-sm font-semibold text-aqua-700 hover:underline";
const LABEL = "text-sm font-semibold text-slate-700";
const INPUT =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-aqua-600";

// 'view' | 'edit' | 'confirm'
const mode = ref("view");
const error = ref("");

const editButton = ref(null);
const removeButton = ref(null);

// Back to the normal row, giving the focus to the button that opened the action
function backToView(button) {
  mode.value = "view";
  nextTick(() => button.value?.focus());
}

// ---------------------------------------------------------------------------
// Editar
// ---------------------------------------------------------------------------
const form = reactive({ name: "" });
const saving = ref(false);
const nameInput = ref(null);

function openEdit() {
  error.value = "";
  form.name = props.user.name;
  mode.value = "edit";
  nextTick(() => nameInput.value?.focus());
}

function closeEdit() {
  error.value = "";
  backToView(editButton);
}

async function saveEdit() {
  if (saving.value) return;
  const name = form.name.trim();
  if (!name) {
    error.value = ERROR_TEXTS.INVALID_NAME;
    nameInput.value?.focus();
    return;
  }

  if (name === props.user.name) {
    closeEdit();
    return;
  }

  saving.value = true;
  error.value = "";
  try {
    // The store replaces the user with the answer, so the row updates itself
    const updated = await usersStore.updateUser(props.user.id, { name });
    backToView(editButton);
    emit("updated", updated);
  } catch (err) {
    error.value = errorText(
      err,
      "No se han podido guardar los cambios. Inténtalo de nuevo.",
    );
  } finally {
    saving.value = false;
  }
}

// ---------------------------------------------------------------------------
// Quitar acceso
// ---------------------------------------------------------------------------
const removing = ref(false);
const cancelButton = ref(null);

function askRemove() {
  error.value = "";
  mode.value = "confirm";
  nextTick(() => cancelButton.value?.focus());
}

function cancelRemove() {
  backToView(removeButton);
}

async function confirmRemove() {
  if (removing.value) return;
  removing.value = true;
  try {
    // On success the user leaves the store and this row disappears
    await props.remove(props.user);
  } catch (err) {
    error.value = errorText(
      err,
      "No se ha podido quitar el acceso. Inténtalo de nuevo.",
    );
    removing.value = false;
    backToView(removeButton);
  }
}
</script>
