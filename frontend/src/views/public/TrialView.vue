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
          class="bg-white border border-aqua-100 rounded-2xl p-6 sm:p-8 shadow-[0_16px_40px_rgba(3,105,161,0.1)]"
        >
          <h2 class="text-2xl font-bold text-aqua-900">Crea tu cuenta</h2>
          <p class="mt-1 mb-6 text-sm text-slate-600">
            Todos los campos son obligatorios.
          </p>

          <!-- novalidate: we show our own Spanish messages next to each field -->
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
                ref="nameInput"
                v-model="form.name"
                type="text"
                autocomplete="name"
                maxlength="120"
                :aria-invalid="Boolean(fieldErrors.name)"
                :aria-describedby="
                  fieldErrors.name ? 'trial-name-error' : undefined
                "
                :class="inputClass('name')"
                placeholder="Nombre y apellidos"
              />
              <p
                v-if="fieldErrors.name"
                id="trial-name-error"
                class="mt-1 text-sm text-danger-dark"
              >
                {{ fieldErrors.name }}
              </p>
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
                ref="emailInput"
                v-model="form.email"
                type="email"
                autocomplete="email"
                inputmode="email"
                :aria-invalid="Boolean(fieldErrors.email)"
                :aria-describedby="
                  fieldErrors.email ? 'trial-email-error' : undefined
                "
                :class="inputClass('email')"
                placeholder="tu@empresa.com"
              />
              <p
                v-if="fieldErrors.email"
                id="trial-email-error"
                class="mt-1 text-sm text-danger-dark"
              >
                {{ fieldErrors.email }}
                <RouterLink
                  v-if="emailTaken"
                  to="/login"
                  class="font-semibold underline hover:no-underline"
                  >Entrar</RouterLink
                >
              </p>
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
                  ref="passwordInput"
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="new-password"
                  maxlength="128"
                  :aria-invalid="Boolean(fieldErrors.password)"
                  :aria-describedby="
                    fieldErrors.password
                      ? 'trial-password-hint trial-password-error'
                      : 'trial-password-hint'
                  "
                  :class="[inputClass('password'), 'pr-20']"
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
              <p
                v-if="fieldErrors.password"
                id="trial-password-error"
                class="mt-1 text-sm text-danger-dark"
              >
                {{ fieldErrors.password }}
              </p>
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
                ref="organizationInput"
                v-model="form.organization_name"
                type="text"
                autocomplete="organization"
                maxlength="120"
                :aria-invalid="Boolean(fieldErrors.organization_name)"
                :aria-describedby="
                  fieldErrors.organization_name
                    ? 'trial-organization-error'
                    : undefined
                "
                :class="inputClass('organization_name')"
                placeholder="Hotel, escuela, comunidad de vecinos..."
              />
              <p
                v-if="fieldErrors.organization_name"
                id="trial-organization-error"
                class="mt-1 text-sm text-danger-dark"
              >
                {{ fieldErrors.organization_name }}
              </p>
            </div>

            <!-- Terms and privacy -->
            <div>
              <div class="flex items-start gap-3">
                <input
                  id="trial-terms"
                  ref="termsInput"
                  v-model="form.accept_terms"
                  type="checkbox"
                  class="mt-1 w-4 h-4 shrink-0 accent-aqua-600 cursor-pointer"
                  :aria-invalid="Boolean(fieldErrors.accept_terms)"
                  :aria-describedby="
                    fieldErrors.accept_terms ? 'trial-terms-error' : undefined
                  "
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
              <p
                v-if="fieldErrors.accept_terms"
                id="trial-terms-error"
                class="mt-1 text-sm text-danger-dark"
              >
                {{ fieldErrors.accept_terms }}
              </p>
            </div>

            <!-- General error (rate limit, network, unexpected) -->
            <div
              v-if="generalError"
              class="bg-danger-light border border-danger text-danger-dark rounded-lg p-3 text-sm"
              role="alert"
            >
              {{ generalError }}
            </div>

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
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../../stores/auth.js";
import PublicLayout from "../../layouts/PublicLayout.vue";
// Same rule as the backend (backend/app/shared/passwords.py) and Mi cuenta.
// The backend also rejects common passwords and passwords containing the email.
import { PASSWORD_MIN_LENGTH } from "../../utils/passwords.js";

const MAX_NAME_LENGTH = 120;

// Where a new client lands after signing up.
// The session is already open: the register response sets the cookie.
const CLIENT_HOME = "/app";

// Simple shape check; the backend does the strict validation.
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

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

// One message per field, shown under the input
const fieldErrors = reactive({
  name: "",
  email: "",
  password: "",
  organization_name: "",
  accept_terms: "",
});

const generalError = ref("");
const emailTaken = ref(false);
const showPassword = ref(false);

// Template refs, used to move the focus to the first field with an error
const nameInput = ref(null);
const emailInput = ref(null);
const passwordInput = ref(null);
const organizationInput = ref(null);
const termsInput = ref(null);

const inputRefs = {
  name: nameInput,
  email: emailInput,
  password: passwordInput,
  organization_name: organizationInput,
  accept_terms: termsInput,
};

// Fields in screen order: the first one with an error gets the focus
const FIELD_ORDER = [
  "name",
  "email",
  "password",
  "organization_name",
  "accept_terms",
];

const isLoading = computed(() => authStore.status === "loading");
const passwordLongEnough = computed(
  () => form.password.length >= PASSWORD_MIN_LENGTH,
);

// Backend error codes that belong to one field
const FIELD_BY_CODE = {
  EMAIL_ALREADY_EXISTS: "email",
  ORGANIZATION_NAME_TAKEN: "organization_name",
  WEAK_PASSWORD: "password",
  INVALID_NAME: "organization_name",
  TERMS_NOT_ACCEPTED: "accept_terms",
};

// Our own Spanish text per code. WEAK_PASSWORD keeps the backend message,
// because it says exactly what is wrong (too short, too common, has the email).
const MESSAGE_BY_CODE = {
  EMAIL_ALREADY_EXISTS: "Ya hay una cuenta con este email.",
  ORGANIZATION_NAME_TAKEN: "Ya hay una empresa registrada con este nombre.",
  INVALID_NAME: "Escribe el nombre de tu empresa.",
  TERMS_NOT_ACCEPTED:
    "Tienes que aceptar los términos y la política de privacidad.",
};

// Messages for the generic 422 VALIDATION_ERROR (Pydantic), by field
const MESSAGE_BY_FIELD = {
  name: `Escribe tu nombre (máximo ${MAX_NAME_LENGTH} caracteres).`,
  email: "Escribe un email válido.",
  password: "Revisa la contraseña.",
  organization_name: `Escribe el nombre de tu empresa (máximo ${MAX_NAME_LENGTH} caracteres).`,
  accept_terms: "Tienes que aceptar los términos y la política de privacidad.",
};

function inputClass(field) {
  const base =
    "w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-aqua-400";
  return fieldErrors[field]
    ? `${base} border-danger bg-danger-light/40`
    : `${base} border-slate-300`;
}

function clearErrors() {
  for (const field of FIELD_ORDER) {
    fieldErrors[field] = "";
  }
  generalError.value = "";
  emailTaken.value = false;
}

// Client-side checks, before calling the API. Returns true when valid.
function validate() {
  const name = form.name.trim();
  const organization = form.organization_name.trim();

  if (!name) {
    fieldErrors.name = "Escribe tu nombre.";
  } else if (name.length > MAX_NAME_LENGTH) {
    fieldErrors.name = MESSAGE_BY_FIELD.name;
  }

  if (!EMAIL_PATTERN.test(form.email.trim())) {
    fieldErrors.email = "Escribe un email válido, por ejemplo tu@empresa.com.";
  }

  if (form.password.length < PASSWORD_MIN_LENGTH) {
    fieldErrors.password = `La contraseña tiene que tener al menos ${PASSWORD_MIN_LENGTH} caracteres.`;
  }

  if (!organization) {
    fieldErrors.organization_name = "Escribe el nombre de tu empresa.";
  } else if (organization.length > MAX_NAME_LENGTH) {
    fieldErrors.organization_name = MESSAGE_BY_FIELD.organization_name;
  }

  if (!form.accept_terms) {
    fieldErrors.accept_terms = MESSAGE_BY_FIELD.accept_terms;
  }

  return FIELD_ORDER.every((field) => !fieldErrors[field]);
}

// Turns an API error (already normalized by the adapter) into field or general messages
function showApiError(err) {
  if (err?.status === 429) {
    generalError.value = "Demasiados intentos, prueba en unos minutos.";
    return;
  }

  const field = FIELD_BY_CODE[err?.code];
  if (field) {
    fieldErrors[field] = MESSAGE_BY_CODE[err.code] ?? err.message;
    emailTaken.value = err.code === "EMAIL_ALREADY_EXISTS";
    return;
  }

  // Generic 422: details = [{ field, message, type }], field without "body."
  if (err?.code === "VALIDATION_ERROR" && Array.isArray(err.details)) {
    let matched = false;
    for (const detail of err.details) {
      if (detail?.field in fieldErrors) {
        fieldErrors[detail.field] = MESSAGE_BY_FIELD[detail.field];
        matched = true;
      }
    }
    if (matched) return;
  }

  if (err?.code === "NETWORK_ERROR") {
    generalError.value =
      "No hemos podido conectar con el servidor. Inténtalo de nuevo.";
    return;
  }

  generalError.value =
    "No hemos podido crear tu cuenta. Inténtalo de nuevo en unos minutos.";
}

async function focusFirstError() {
  await nextTick();
  const field = FIELD_ORDER.find((name) => fieldErrors[name]);
  inputRefs[field]?.value?.focus();
}

async function handleSubmit() {
  if (isLoading.value) return;

  clearErrors();
  authStore.clearError();

  if (!validate()) {
    await focusFirstError();
    return;
  }

  try {
    // The store keeps the user from the response (SessionResponse),
    // so there is no need to call /api/me afterwards.
    await authStore.register({
      name: form.name.trim(),
      email: form.email.trim(),
      password: form.password,
      organization_name: form.organization_name.trim(),
      accept_terms: form.accept_terms,
    });

    await router.replace(CLIENT_HOME);
  } catch (err) {
    showApiError(err);
    await focusFirstError();
  }
}

// Clear a field's error as soon as the user edits that field
for (const field of FIELD_ORDER) {
  watch(
    () => form[field],
    () => {
      fieldErrors[field] = "";
      if (field === "email") emailTaken.value = false;
    },
  );
}

onMounted(() => {
  authStore.clearError();
});
</script>
