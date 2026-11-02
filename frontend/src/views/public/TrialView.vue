<template>
  <PublicLayout>
    <section
      class="flex-1 bg-gradient-to-b from-aqua-100 to-aqua-50 px-4 py-12 sm:px-6 md:px-20 md:py-16"
    >
      <div
        class="max-w-5xl mx-auto grid gap-10 items-start md:grid-cols-[1fr_1.1fr]"
      >
        <!-- Left column: what the trial includes -->
        <div class="flex flex-col gap-5 md:pt-6">
          <p class="text-xs font-bold uppercase tracking-widest text-aqua-600">
            Prueba gratis de 7 días
          </p>
          <h1
            class="text-3xl md:text-4xl font-bold leading-tight text-aqua-900"
          >
            Empieza a vigilar el agua de tu edificio hoy mismo.
          </h1>
          <p class="text-lg text-slate-700">
            Crea tu cuenta y la de tu empresa en un paso. Entrarás directamente
            a tu panel.
          </p>

          <ul class="flex flex-col gap-3" aria-label="Qué incluye la prueba">
            <li
              v-for="benefit in benefits"
              :key="benefit"
              class="flex items-start gap-3 text-slate-700"
            >
              <span
                class="mt-1 w-5 h-5 shrink-0 rounded-full bg-aqua-600 text-white text-xs font-bold flex items-center justify-center"
                aria-hidden="true"
                >✓</span
              >
              <span>{{ benefit }}</span>
            </li>
          </ul>
        </div>

        <!-- Right column: sign-up form -->
        <div
          class="bg-white border border-aqua-100 rounded-2xl p-6 sm:p-8 shadow-[0_16px_40px_theme(colors.aqua.600/10%)]"
        >
          <h2 class="text-2xl font-bold text-aqua-900">Crea tu cuenta</h2>
          <p class="mt-1 mb-6 text-sm text-slate-600">
            Todos los campos son obligatorios.
          </p>

          <!-- novalidate: our own Spanish messages, the same in every form -->
          <form novalidate class="space-y-5" @submit.prevent="handleSubmit">
            <!-- Name -->
            <div>
              <label
                for="trial-name"
                class="block text-sm font-medium text-slate-700 mb-1"
              >
                Tu nombre
              </label>
              <input
                id="trial-name"
                :ref="setRef('name')"
                v-model="form.name"
                type="text"
                autocomplete="name"
                :maxlength="FIELD_LIMITS.username"
                :class="inputClass('name')"
                v-bind="fieldAttrs('name')"
                placeholder="Nombre y apellidos"
              />
              <FieldError :id="errorId('name')" :message="errors.name" />
            </div>

            <!-- Email -->
            <div>
              <label
                for="trial-email"
                class="block text-sm font-medium text-slate-700 mb-1"
              >
                Email
              </label>
              <input
                id="trial-email"
                :ref="setRef('email')"
                v-model="form.email"
                type="email"
                autocomplete="email"
                inputmode="email"
                :maxlength="FIELD_LIMITS.email"
                :class="inputClass('email')"
                v-bind="fieldAttrs('email')"
                placeholder="tu@empresa.com"
              />
              <FieldError :id="errorId('email')" :message="errors.email">
                <RouterLink
                  v-if="emailTaken"
                  to="/login"
                  class="font-semibold underline hover:no-underline"
                  >Entrar</RouterLink
                >
              </FieldError>
            </div>

            <!-- Password -->
            <div>
              <label
                for="trial-password"
                class="block text-sm font-medium text-slate-700 mb-1"
              >
                Contraseña
              </label>
              <div class="relative">
                <input
                  id="trial-password"
                  :ref="setRef('password')"
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="new-password"
                  :class="inputClass('password', 'pr-20')"
                  v-bind="fieldAttrs('password', 'trial-password-hint')"
                />
                <button
                  type="button"
                  class="absolute inset-y-0 right-0 px-3 text-sm font-semibold text-aqua-700 hover:underline"
                  :aria-pressed="showPassword"
                  @click="showPassword = !showPassword"
                >
                  {{ showPassword ? "Ocultar" : "Mostrar" }}
                </button>
              </div>
              <p id="trial-password-hint" class="mt-1 text-xs text-slate-600">
                Mínimo {{ PASSWORD_MIN_LENGTH }} caracteres. Evita contraseñas
                comunes y no incluyas tu email.
                <span
                  :class="
                    passwordLongEnough ? 'text-success-dark font-semibold' : ''
                  "
                >
                  ({{ form.password.length }}/{{ PASSWORD_MIN_LENGTH }})
                </span>
              </p>
              <FieldError :id="errorId('password')" :message="errors.password" />
            </div>

            <!-- Company name -->
            <div>
              <label
                for="trial-organization"
                class="block text-sm font-medium text-slate-700 mb-1"
              >
                Nombre de la empresa
              </label>
              <input
                id="trial-organization"
                :ref="setRef('organization_name')"
                v-model="form.organization_name"
                type="text"
                autocomplete="organization"
                :maxlength="FIELD_LIMITS.organizationName"
                :class="inputClass('organization_name')"
                v-bind="fieldAttrs('organization_name')"
                placeholder="Hotel, escuela, comunidad de vecinos..."
              />
              <FieldError
                :id="errorId('organization_name')"
                :message="errors.organization_name"
              />
            </div>

            <!-- Terms and privacy -->
            <div>
              <div class="flex items-start gap-3">
                <input
                  id="trial-terms"
                  :ref="setRef('accept_terms')"
                  v-model="form.accept_terms"
                  type="checkbox"
                  class="mt-1 w-4 h-4 shrink-0 accent-aqua-600 cursor-pointer"
                  v-bind="fieldAttrs('accept_terms')"
                />
                <label for="trial-terms" class="text-sm text-slate-700">
                  He leído y acepto los
                  <a
                    href="/legal#terminos"
                    target="_blank"
                    rel="noopener"
                    class="font-semibold text-aqua-700 underline hover:no-underline"
                    >términos de uso</a
                  >
                  y la
                  <a
                    href="/legal#privacidad"
                    target="_blank"
                    rel="noopener"
                    class="font-semibold text-aqua-700 underline hover:no-underline"
                    >política de privacidad</a
                  >.
                  <span class="sr-only">(se abren en una pestaña nueva)</span>
                </label>
              </div>
              <FieldError
                :id="errorId('accept_terms')"
                :message="errors.accept_terms"
              />
            </div>

            <!-- General error (rate limit, network, unexpected) -->
            <FormError :message="generalError" />

            <button
              type="submit"
              :disabled="isLoading"
              class="w-full bg-aqua-600 text-white font-semibold py-3 rounded-lg hover:bg-aqua-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{
                isLoading ? "Creando tu cuenta..." : "Empezar la prueba gratis"
              }}
            </button>
          </form>

          <p class="text-center text-sm text-slate-600 mt-6">
            ¿Ya tienes una cuenta?
            <RouterLink
              to="/login"
              class="text-aqua-700 font-semibold hover:underline"
            >
              Entrar
            </RouterLink>
          </p>
        </div>
      </div>
    </section>
  </PublicLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../../stores/auth.js";
import PublicLayout from "../../layouts/PublicLayout.vue";
import FieldError from "../../components/FieldError.vue";
import FormError from "../../components/FormError.vue";
import { useFieldErrors } from "../../composables/useFieldErrors.js";
import { apiErrorMessage } from "../../utils/apiError.js";
import { FIELD_LIMITS } from "../../utils/limits.js";
// Same rule as the backend (backend/app/shared/passwords.py) and Mi cuenta.
// The backend also rejects common passwords and passwords containing the email.
import {
  PASSWORD_MIN_LENGTH,
  passwordProblem,
} from "../../utils/passwords.js";
// Same name and email rules as every other form (utils/validation.js)
import {
  cleanText,
  emailProblem,
  organizationNameProblem,
  personNameProblem,
} from "../../utils/validation.js";

// Where a new client lands after signing up.
// The session is already open: the register response sets the cookie.
const CLIENT_HOME = "/app";

const TERMS_MESSAGE =
  "Tienes que aceptar los términos y la política de privacidad.";

const benefits = [
  "7 días gratis, sin tarjeta.",
  "Tu panel listo nada más registrarte.",
  "Avisos al momento si cambia la presión del agua.",
  "Para edificios de Barcelona.",
];

const router = useRouter();
const authStore = useAuthStore();

const form = reactive({
  name: "",
  email: "",
  password: "",
  organization_name: "",
  accept_terms: false,
});

// Fields in screen order: the first one with an error gets the focus
const {
  errors,
  errorId,
  setRef,
  inputClass,
  fieldAttrs,
  clear,
  check,
  focusFirstError,
  clearOnEdit,
  applyApiError,
} = useFieldErrors(
  ["name", "email", "password", "organization_name", "accept_terms"],
  { size: "lg" },
);
clearOnEdit({
  name: () => form.name,
  email: () => form.email,
  password: () => form.password,
  organization_name: () => form.organization_name,
  accept_terms: () => form.accept_terms,
});

const generalError = ref("");
const emailTaken = ref(false);
const showPassword = ref(false);

watch(
  () => form.email,
  () => {
    emailTaken.value = false;
  },
);

const isLoading = computed(() => authStore.status === "loading");
const passwordLongEnough = computed(
  () => form.password.length >= PASSWORD_MIN_LENGTH,
);

// API errors of one field. WEAK_PASSWORD and INVALID_NAME keep the backend
// message, which says exactly what is wrong; INVALID_NAME says the field
// (name or organization_name) in details
const API_ERRORS = {
  codes: {
    EMAIL_ALREADY_EXISTS: {
      field: "email",
      message: "Ya hay una cuenta con este email.",
    },
    ORGANIZATION_NAME_TAKEN: {
      field: "organization_name",
      message: "Ya hay una empresa registrada con este nombre.",
    },
    WEAK_PASSWORD: "password",
    TERMS_NOT_ACCEPTED: { field: "accept_terms", message: TERMS_MESSAGE },
  },
  messages: {
    name: `Escribe tu nombre (máximo ${FIELD_LIMITS.username} caracteres).`,
    email: "Escribe un email válido, por ejemplo nombre@empresa.com.",
    password: "Revisa la contraseña.",
    organization_name: `Escribe el nombre de tu empresa (máximo ${FIELD_LIMITS.organizationName} caracteres).`,
    accept_terms: TERMS_MESSAGE,
  },
};

async function handleSubmit() {
  if (isLoading.value) return;

  clear();
  generalError.value = "";
  authStore.clearError();

  const valid = check({
    name: () => personNameProblem(form.name),
    email: () => emailProblem(form.email),
    password: () => passwordProblem(form.password, form.email),
    organization_name: () => organizationNameProblem(form.organization_name),
    accept_terms: () => (form.accept_terms ? null : TERMS_MESSAGE),
  });
  if (!valid) {
    await focusFirstError();
    return;
  }

  try {
    // The store keeps the user from the response (SessionResponse),
    // so there is no need to call /api/me afterwards.
    await authStore.register({
      name: cleanText(form.name),
      email: form.email.trim(),
      password: form.password,
      organization_name: cleanText(form.organization_name),
      accept_terms: form.accept_terms,
    });

    await router.replace(CLIENT_HOME);
  } catch (err) {
    if (applyApiError(err, API_ERRORS)) {
      emailTaken.value = err.code === "EMAIL_ALREADY_EXISTS";
      await focusFirstError();
      return;
    }
    generalError.value = apiErrorMessage(
      err,
      "No hemos podido crear tu cuenta. Inténtalo de nuevo en unos minutos.",
    );
  }
}

onMounted(() => {
  authStore.clearError();
});
</script>
