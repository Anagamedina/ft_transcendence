<template>
  <div class="space-y-6">
    <h1 class="text-3xl font-bold text-slate-900">Mi cuenta</h1>

    <!-- Two columns on desktop, one on mobile. Extra cards come from the slots:
         the client view adds Suscripción and Privacidad, the admin view adds nothing.
         No "Sesión" card: both layouts already have "Cerrar sesión" (F27). -->
    <div class="grid items-start gap-6 lg:grid-cols-2">
      <section
        class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        aria-labelledby="profile-title"
      >
        <h2 id="profile-title" class="mb-4 text-lg font-bold text-slate-800">
          Datos personales
        </h2>
        <form class="space-y-4" @submit.prevent="saveProfile">
          <div>
            <label
              for="account-name"
              class="block text-sm font-medium text-slate-700"
              >Nombre</label
            >
            <input
              id="account-name"
              v-model="name"
              required
              maxlength="120"
              autocomplete="name"
              :disabled="trialExpired"
              class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 disabled:bg-slate-50 disabled:text-slate-600"
              @input="
                profileSaved = false;
                profileError = '';
              "
            />
          </div>
          <div>
            <label
              for="account-email"
              class="block text-sm font-medium text-slate-700"
              >Email</label
            >
            <input
              id="account-email"
              :value="authStore.user?.email"
              readonly
              aria-describedby="account-email-hint"
              class="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-slate-600"
            />
            <p id="account-email-hint" class="mt-1 text-xs text-slate-600">
              El email no se puede cambiar.
            </p>
          </div>
          <p class="text-xs text-slate-600">
            <template v-if="authStore.isAdmin">Rol: Administrador · </template>
            <!-- The backend sets last_login_at on every login -->
            Último inicio de sesión: {{ formatDateTime(authStore.lastLoginAt) }}
          </p>
          <p v-if="profileError" class="text-sm text-danger-dark" role="alert">
            {{ profileError }}
          </p>
          <p v-if="profileSaved" class="text-sm text-success-dark" role="status">
            Datos actualizados.
          </p>
          <button
            type="submit"
            :disabled="trialExpired || profileLoading"
            class="rounded-lg bg-aqua-600 px-4 py-2 font-semibold text-white disabled:opacity-50"
          >
            {{ profileLoading ? "Guardando…" : "Guardar cambios" }}
          </button>
          <p v-if="trialExpired" class="text-xs text-slate-600">
            No disponible con la prueba terminada.
          </p>
        </form>
      </section>

      <slot name="after-profile" />

      <section
        class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        aria-labelledby="password-title"
      >
        <h2 id="password-title" class="mb-4 text-lg font-bold text-slate-800">
          Cambiar contraseña
        </h2>
        <form class="space-y-4" @submit.prevent="savePassword">
          <div v-for="field in passwordFields" :key="field.key">
            <label
              :for="`account-${field.key}`"
              class="block text-sm font-medium text-slate-700"
              >{{ field.label }}</label
            >
            <div class="relative mt-1">
              <input
                :id="`account-${field.key}`"
                v-model="password[field.key]"
                :type="visible[field.key] ? 'text' : 'password'"
                required
                :maxlength="PASSWORD_MAX_LENGTH"
                :disabled="trialExpired"
                :minlength="
                  field.key === 'current_password'
                    ? undefined
                    : PASSWORD_MIN_LENGTH
                "
                :autocomplete="
                  field.key === 'current_password'
                    ? 'current-password'
                    : 'new-password'
                "
                :aria-describedby="
                  field.key === 'new_password'
                    ? 'account-password-hint'
                    : undefined
                "
                class="w-full rounded-lg border border-slate-300 px-3 py-2 pr-20 disabled:bg-slate-50"
                @input="
                  passwordSaved = false;
                  passwordError = '';
                "
              />
              <!-- Same show / hide button as the sign-up form (/prueba) -->
              <button
                type="button"
                class="absolute inset-y-0 right-0 px-3 text-sm font-semibold text-aqua-700 hover:underline disabled:opacity-50"
                :disabled="trialExpired"
                :aria-pressed="visible[field.key]"
                :aria-label="`${visible[field.key] ? 'Ocultar' : 'Mostrar'} ${field.label.toLowerCase()}`"
                @click="visible[field.key] = !visible[field.key]"
              >
                {{ visible[field.key] ? "Ocultar" : "Mostrar" }}
              </button>
            </div>
            <p
              v-if="field.key === 'new_password'"
              id="account-password-hint"
              class="mt-1 text-xs text-slate-600"
            >
              Mínimo {{ PASSWORD_MIN_LENGTH }} caracteres y sin tu email, la
              misma regla que el registro.
              <span
                :class="
                  password.new_password.length >= PASSWORD_MIN_LENGTH
                    ? 'font-semibold text-success-dark'
                    : ''
                "
              >
                ({{ password.new_password.length }}/{{ PASSWORD_MIN_LENGTH }})
              </span>
            </p>
          </div>
          <p v-if="passwordError" class="text-sm text-danger-dark" role="alert">
            {{ passwordError }}
          </p>
          <p
            v-if="passwordSaved"
            role="status"
            class="rounded-lg border border-success-light bg-success-light px-3 py-2 text-sm text-success-dark"
          >
            Contraseña cambiada. La próxima vez entra con la nueva.
          </p>
          <button
            type="submit"
            :disabled="trialExpired || passwordLoading"
            class="rounded-lg bg-aqua-600 px-4 py-2 font-semibold text-white disabled:opacity-50"
          >
            {{ passwordLoading ? "Actualizando…" : "Cambiar contraseña" }}
          </button>
          <p v-if="trialExpired" class="text-xs text-slate-600">
            No disponible con la prueba terminada.
          </p>
        </form>
      </section>

      <slot name="after-password" />

    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useAuthStore } from "../stores/auth";
import { formatDateTime } from "../composables/useFormat";
import { useClientStatus } from "../composables/useClientStatus";
// Same rule as the sign-up form (/prueba) and the backend (B10)
import {
  PASSWORD_MAX_LENGTH,
  PASSWORD_MIN_LENGTH,
  loginPasswordProblem,
  passwordProblem,
} from "../utils/passwords";
import { apiErrorMessage } from "../utils/apiError";

const authStore = useAuthStore();
// Expired trial: the backend answers 403 TRIAL_EXPIRED to both forms (B12), so they
// are disabled; TrialBanner in ClientLayout already explains why.
// Only a client's organization can be on an expired trial
const trialExpired = computed(
  () =>
    authStore.isClient &&
    Boolean(authStore.organization) &&
    useClientStatus(authStore.organization).trialEnded,
);
const name = ref(authStore.user?.name ?? "");
const profileLoading = ref(false);
const profileError = ref("");
const profileSaved = ref(false);
const passwordLoading = ref(false);
const passwordError = ref("");
const passwordSaved = ref(false);
const password = ref({
  current_password: "",
  new_password: "",
  confirmation: "",
});
// Which password fields are shown as plain text (all hidden by default)
const visible = ref({
  current_password: false,
  new_password: false,
  confirmation: false,
});
const passwordFields = [
  { key: "current_password", label: "Contraseña actual" },
  { key: "new_password", label: "Contraseña nueva" },
  { key: "confirmation", label: "Repite la contraseña nueva" },
];

watch(
  () => authStore.user?.name,
  (value) => {
    if (value) name.value = value;
  },
);

async function saveProfile() {
  profileError.value = "";
  profileSaved.value = false;
  // Only spaces passes `required`; the backend trims and would answer a generic 422
  const trimmed = name.value.trim();
  if (!trimmed) {
    profileError.value = "Escribe tu nombre.";
    return;
  }
  profileLoading.value = true;
  try {
    await authStore.updateMe({ name: trimmed });
    profileSaved.value = true;
  } catch (error) {
    profileError.value = apiErrorMessage(
      error,
      "No se han podido guardar los datos.",
    );
  } finally {
    profileLoading.value = false;
  }
}

async function savePassword() {
  passwordError.value = "";
  passwordSaved.value = false;
  const problem =
    loginPasswordProblem(password.value.current_password) ??
    passwordProblem(password.value.new_password, authStore.user?.email ?? "");
  if (problem) {
    passwordError.value = problem;
    return;
  }
  if (password.value.new_password !== password.value.confirmation) {
    passwordError.value = "Las contraseñas nuevas no coinciden.";
    return;
  }
  passwordLoading.value = true;
  try {
    await authStore.changePassword({
      current_password: password.value.current_password,
      new_password: password.value.new_password,
    });
    password.value = {
      current_password: "",
      new_password: "",
      confirmation: "",
    };
    visible.value = {
      current_password: false,
      new_password: false,
      confirmation: false,
    };
    passwordSaved.value = true;
  } catch (error) {
    passwordError.value =
      error.code === "WRONG_PASSWORD"
        ? "La contraseña actual no es correcta."
        : error.code === "WEAK_PASSWORD"
          ? error.message
          : apiErrorMessage(error, "No se ha podido cambiar la contraseña.");
  } finally {
    passwordLoading.value = false;
  }
}
</script>
