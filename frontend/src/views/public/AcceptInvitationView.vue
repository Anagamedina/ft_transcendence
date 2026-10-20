<template>
  <PublicLayout>
    <section
      class="flex-1 bg-gradient-to-b from-aqua-100 to-aqua-50 px-4 py-12 sm:px-6 md:py-16"
    >
      <div class="max-w-md mx-auto">
        <!-- Loading the invitation -->
        <LoadingState
          v-if="state === 'loading'"
          message="Comprobando la invitación…"
        />

        <!-- The invitation could not be loaded (network, server, rate limit) -->
        <ErrorState
          v-else-if="state === 'error'"
          title="No hemos podido abrir la invitación"
          :message="loadError"
          :autofocus="retried"
          @retry="retryLoad"
        />

        <!-- No code in the URL: the person pastes the link they received -->
        <form
          v-else-if="state === 'missing'"
          novalidate
          :class="[CARD, 'space-y-4']"
          @submit.prevent="useLink"
        >
          <h1 class="text-2xl font-bold text-aqua-900">
            Aceptar una invitación
          </h1>
          <div>
            <label
              for="invite-link"
              class="block text-sm font-medium text-slate-700 mb-1"
            >
              Pega el enlace que has recibido por email
            </label>
            <input
              id="invite-link"
              ref="linkInput"
              v-model="pastedLink"
              type="text"
              inputmode="url"
              autocomplete="off"
              spellcheck="false"
              :aria-invalid="Boolean(linkError)"
              :aria-describedby="linkError ? 'invite-link-error' : undefined"
              :class="[linkError ? INPUT_ERROR : INPUT, 'font-mono text-sm']"
              placeholder="https://…/registro?invitacion=…"
            />
            <p
              v-if="linkError"
              id="invite-link-error"
              class="mt-1 text-sm text-danger-dark"
            >
              {{ linkError }}
            </p>
          </div>
          <button type="submit" :class="BUTTON_PRIMARY">Continuar</button>
        </form>

        <!-- The link cannot be used: expired (410) or not found / used / revoked (404) -->
        <div
          v-else-if="state === 'expired' || state === 'not_found'"
          :class="[CARD, 'text-center flex flex-col items-center gap-3']"
        >
          <span
            class="w-14 h-14 rounded-full flex items-center justify-center"
            :class="state === 'expired' ? 'bg-warning-light' : 'bg-slate-100'"
            aria-hidden="true"
          >
            <svg
              v-if="state === 'expired'"
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              class="text-warning-dark"
              stroke-width="2"
              stroke-linecap="round"
            >
              <circle cx="12" cy="12" r="9" />
              <polyline points="12 7 12 12 15 14" />
            </svg>
            <svg
              v-else
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              class="text-slate-600"
              stroke-width="2"
              stroke-linecap="round"
            >
              <circle cx="12" cy="12" r="9" />
              <line x1="12" y1="8" x2="12" y2="13" />
              <line x1="12" y1="16.5" x2="12" y2="16.5" />
            </svg>
          </span>
          <h1
            ref="problemHeading"
            tabindex="-1"
            class="text-2xl font-bold text-aqua-900 focus:outline-none"
          >
            {{ problem.title }}
          </h1>
          <p class="text-slate-700">{{ problem.text }}</p>
          <RouterLink
            v-if="state === 'not_found'"
            to="/login"
            :class="[BUTTON_PRIMARY, 'mt-2']"
          >
            Entrar
          </RouterLink>
        </div>

        <!-- Account created: the session is open -->
        <div
          v-else-if="state === 'done'"
          :class="[CARD, 'text-center flex flex-col items-center gap-3']"
        >
          <span
            class="w-14 h-14 rounded-full bg-success-light flex items-center justify-center"
            aria-hidden="true"
          >
            <svg
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              class="text-success-dark"
              stroke-width="2.5"
              stroke-linecap="round"
            >
              <polyline points="5 12 10 17 19 7" />
            </svg>
          </span>
          <h1
            ref="doneHeading"
            tabindex="-1"
            class="text-2xl font-bold text-aqua-900 focus:outline-none"
          >
            Tu cuenta está lista
          </h1>
          <p class="text-slate-700">
            <template v-if="invitation.organization_name">
              Ya formas parte de {{ invitation.organization_name }}.
            </template>
            <template v-else>Ya formas parte de AquaGuard.</template>
          </p>
          <RouterLink :to="CLIENT_HOME" :class="[BUTTON_PRIMARY, 'mt-2']"
            >Ir a mi panel</RouterLink
          >
        </div>

        <!-- Valid invitation: the accept form -->
        <div v-else :class="CARD">
          <h1 class="text-2xl font-bold text-aqua-900">
            <template v-if="invitation.organization_name">
              Únete a {{ invitation.organization_name }}
            </template>
            <template v-else>Únete a AquaGuard</template>
          </h1>
          <p class="mt-1 text-sm text-slate-600">
            Crea tu contraseña para entrar en AquaGuard. La invitación vale
            hasta el
            <time :datetime="invitation.expires_at" class="font-semibold">{{
              expiresText
            }}</time
            >.
          </p>

          <!-- Someone is already logged in in this browser: log out first -->
          <div
            v-if="authStore.isAuthenticated"
            class="mt-5 bg-warning-light border border-warning text-warning-dark rounded-lg p-3 text-sm"
            role="status"
          >
            <p>
              Ahora tienes la sesión abierta como
              <strong>{{ authStore.user?.email }}</strong
              >. Para aceptar esta invitación, cierra antes la sesión.
            </p>
            <button
              type="button"
              class="mt-2 font-semibold underline hover:no-underline"
              :disabled="isLoading"
              @click="logout"
            >
              Cerrar sesión
            </button>
          </div>

          <!-- novalidate: we show our own Spanish messages next to each field -->
          <form
            novalidate
            class="mt-6 space-y-5"
            @submit.prevent="handleSubmit"
          >
            <!-- Email: fixed by the invitation, only shown. Also read by password managers -->
            <div>
              <label
                for="invite-email"
                class="block text-sm font-medium text-slate-700 mb-1"
              >
                Email
              </label>
              <input
                id="invite-email"
                :value="invitation.email"
                type="email"
                autocomplete="username"
                readonly
                aria-describedby="invite-email-hint"
                class="w-full px-4 py-3 border border-slate-200 rounded-lg bg-slate-100 text-slate-600 cursor-default focus:outline-none focus:ring-2 focus:ring-aqua-400"
              />
              <p id="invite-email-hint" class="mt-1 text-xs text-slate-500">
                Viene de la invitación, no se puede cambiar.
              </p>
            </div>

            <!-- Name -->
            <div>
              <label
                for="invite-name"
                class="block text-sm font-medium text-slate-700 mb-1"
              >
                Tu nombre
              </label>
              <input
                id="invite-name"
                ref="nameInput"
                v-model="form.name"
                type="text"
                autocomplete="name"
                maxlength="120"
                :aria-invalid="Boolean(fieldErrors.name)"
                :aria-describedby="
                  fieldErrors.name ? 'invite-name-error' : undefined
                "
                :class="inputClass('name')"
                placeholder="Nombre y apellidos"
              />
              <p
                v-if="fieldErrors.name"
                id="invite-name-error"
                class="mt-1 text-sm text-danger-dark"
              >
                {{ fieldErrors.name }}
              </p>
            </div>

            <!-- Password -->
            <div>
              <label
                for="invite-password"
                class="block text-sm font-medium text-slate-700 mb-1"
              >
                Contraseña (mínimo {{ PASSWORD_MIN_LENGTH }} caracteres)
              </label>
              <div class="relative">
                <input
                  id="invite-password"
                  ref="passwordInput"
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="new-password"
                  maxlength="128"
                  :aria-invalid="Boolean(fieldErrors.password)"
                  :aria-describedby="
                    fieldErrors.password
                      ? 'invite-password-hint invite-password-error'
                      : 'invite-password-hint'
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
              <p id="invite-password-hint" class="mt-1 text-xs text-slate-600">
                Evita contraseñas comunes y no incluyas tu email.
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
                id="invite-password-error"
                class="mt-1 text-sm text-danger-dark"
              >
                {{ fieldErrors.password }}
              </p>
            </div>

            <!-- Terms and privacy -->
            <div>
              <div class="flex items-start gap-3">
                <input
                  id="invite-terms"
                  ref="termsInput"
                  v-model="form.accept_terms"
                  type="checkbox"
                  class="mt-1 w-4 h-4 shrink-0 accent-aqua-600 cursor-pointer"
                  :aria-invalid="Boolean(fieldErrors.accept_terms)"
                  :aria-describedby="
                    fieldErrors.accept_terms ? 'invite-terms-error' : undefined
                  "
                />
                <label for="invite-terms" class="text-sm text-slate-700">
                  Acepto los
                  <a
                    href="/legal#terminos"
                    target="_blank"
                    rel="noopener"
                    class="font-semibold text-aqua-700 underline hover:no-underline"
                    >términos</a
                  >
                  y la
                  <a
                    href="/legal#privacidad"
                    target="_blank"
                    rel="noopener"
                    class="font-semibold text-aqua-700 underline hover:no-underline"
                    >privacidad</a
                  >.
                  <span class="sr-only">(se abren en una pestaña nueva)</span>
                </label>
              </div>
              <p
                v-if="fieldErrors.accept_terms"
                id="invite-terms-error"
                class="mt-1 text-sm text-danger-dark"
              >
                {{ fieldErrors.accept_terms }}
              </p>
            </div>

            <!-- General error (account exists, rate limit, network, unexpected) -->
            <div
              v-if="generalError"
              class="bg-danger-light border border-danger text-danger-dark rounded-lg p-3 text-sm"
              role="alert"
            >
              {{ generalError }}
              <RouterLink
                v-if="emailTaken"
                to="/login"
                class="font-semibold underline hover:no-underline"
                >Entrar</RouterLink
              >
            </div>

            <button
              type="submit"
              :disabled="isLoading || authStore.isAuthenticated"
              :class="BUTTON_PRIMARY"
            >
              {{ isLoading ? "Creando tu cuenta..." : "Crear cuenta" }}
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
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../../stores/auth.js";
import invitationsService from "../../services/invitations.service.js";
import PublicLayout from "../../layouts/PublicLayout.vue";
import LoadingState from "../../components/LoadingState.vue";
import ErrorState from "../../components/ErrorState.vue";
// Same rule as the backend (backend/app/shared/passwords.py), /prueba and Mi cuenta.
// The backend also rejects common passwords.
import { PASSWORD_MIN_LENGTH } from "../../utils/passwords.js";

const MAX_NAME_LENGTH = 120;

// Where the new client lands. The session is already open: the accept
// response sets the cookie, as the register one does.
const CLIENT_HOME = "/dashboard";

// Shared classes, as in the mockup (pantallas/Invitacion.html)
const CARD =
  "bg-white border border-aqua-100 rounded-2xl p-6 sm:p-8 shadow-[0_16px_40px_theme(colors.aqua.600/10%)]";
const INPUT =
  "w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-aqua-400";
const INPUT_ERROR =
  "w-full px-4 py-3 border border-danger bg-danger-light/40 rounded-lg focus:outline-none focus:ring-2 focus:ring-aqua-400";
const BUTTON_PRIMARY =
  "w-full inline-flex justify-center bg-aqua-600 text-white font-semibold py-3 rounded-lg hover:bg-aqua-700 transition disabled:opacity-50 disabled:cursor-not-allowed";

// Texts for the links that cannot be used
const PROBLEMS = {
  not_found: {
    title: "Este enlace ya no es válido",
    text: "La invitación no existe, ya se ha usado o se ha anulado. Si ya creaste tu cuenta, entra con tu email. Si no, pide a tu administrador que te envíe una nueva.",
  },
  expired: {
    title: "Esta invitación ha caducado",
    text: "Las invitaciones duran 7 días. Pide a tu administrador que te envíe una nueva.",
  },
};

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

// loading | missing | not_found | expired | error | ready | done
const state = ref("loading");
const invitation = ref(null);
const loadError = ref("");
const retried = ref(false);

const form = reactive({
  name: "",
  password: "",
  accept_terms: false,
});

// One message per field, shown under the input
const fieldErrors = reactive({
  name: "",
  password: "",
  accept_terms: "",
});

const generalError = ref("");
const emailTaken = ref(false);
const showPassword = ref(false);

// "Sin código en la URL": the link (or bare code) the person pastes
const pastedLink = ref("");
const linkError = ref("");

// Template refs, used to move the focus to the first field with an error
const nameInput = ref(null);
const passwordInput = ref(null);
const termsInput = ref(null);
const problemHeading = ref(null);
const doneHeading = ref(null);
const linkInput = ref(null);

const inputRefs = {
  name: nameInput,
  password: passwordInput,
  accept_terms: termsInput,
};

// Fields in screen order: the first one with an error gets the focus
const FIELD_ORDER = ["name", "password", "accept_terms"];

// The code from ?invitacion=CODE. With a repeated param, the first one
const code = computed(() => {
  const value = route.query.invitacion;
  const first = Array.isArray(value) ? value[0] : value;
  return typeof first === "string" ? first.trim() : "";
});

const problem = computed(() => PROBLEMS[state.value] ?? PROBLEMS.not_found);
const isLoading = computed(() => authStore.status === "loading");
const passwordLongEnough = computed(
  () => form.password.length >= PASSWORD_MIN_LENGTH,
);

const expiresText = computed(() =>
  invitation.value
    ? new Intl.DateTimeFormat("es-ES", { dateStyle: "long" }).format(
        new Date(invitation.value.expires_at),
      )
    : "",
);

// Our own Spanish text per code. WEAK_PASSWORD keeps the backend message,
// because it says exactly what is wrong (too short, too common, has the email).
const MESSAGE_BY_CODE = {
  TERMS_NOT_ACCEPTED:
    "Tienes que aceptar los términos y la política de privacidad.",
};

const FIELD_BY_CODE = {
  WEAK_PASSWORD: "password",
  TERMS_NOT_ACCEPTED: "accept_terms",
};

// Messages for the generic 422 VALIDATION_ERROR (Pydantic), by field
const MESSAGE_BY_FIELD = {
  name: `Escribe tu nombre (máximo ${MAX_NAME_LENGTH} caracteres).`,
  password: "Revisa la contraseña.",
  accept_terms: "Tienes que aceptar los términos y la política de privacidad.",
};

function inputClass(field) {
  return fieldErrors[field] ? INPUT_ERROR : INPUT;
}

// Gets the code from a pasted link (?invitacion=CODE) or from a bare code
function codeFromPastedText(text) {
  const value = text.trim();
  if (!value) return "";
  try {
    // The base makes relative links like /registro?invitacion=... work too
    const url = new URL(value, window.location.origin);
    const fromQuery = url.searchParams.get("invitacion");
    if (fromQuery) return fromQuery.trim();
  } catch {
    // Not a URL: treated as a bare code below
  }
  return /^[\w-]+$/.test(value) ? value : "";
}

// "Continuar": puts the code in the URL; the watch on `code` loads the invitation
async function useLink() {
  const pasted = codeFromPastedText(pastedLink.value);
  if (!pasted) {
    linkError.value =
      "No encontramos el código. Pega el enlace completo del email.";
    await nextTick();
    linkInput.value?.focus();
    return;
  }
  linkError.value = "";
  await router.replace({ query: { invitacion: pasted } });
}

// The link cannot be used: show the problem screen and move the focus to its title
async function showProblem(kind) {
  state.value = kind;
  await nextTick();
  problemHeading.value?.focus();
}

// 404 and 410 mean the link cannot be used, both when loading and when accepting.
// Returns true when the error was one of them.
function handleLinkError(err) {
  if (err?.status === 410 || err?.code === "INVITATION_EXPIRED") {
    showProblem("expired");
    return true;
  }
  if (err?.status === 404 || err?.code === "INVITATION_NOT_FOUND") {
    showProblem("not_found");
    return true;
  }
  return false;
}

async function loadInvitation() {
  if (!code.value) {
    state.value = "missing";
    return;
  }

  state.value = "loading";
  loadError.value = "";

  try {
    const response = await invitationsService.getInvitationByCode(code.value);
    invitation.value = response.data;
    state.value = "ready";
  } catch (err) {
    if (handleLinkError(err)) return;

    loadError.value =
      err?.status === 429
        ? "Demasiados intentos, prueba en unos minutos."
        : "Comprueba la conexión e inténtalo de nuevo.";
    state.value = "error";
  }
}

function retryLoad() {
  retried.value = true;
  loadInvitation();
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

  if (!name) {
    fieldErrors.name = "Escribe tu nombre.";
  } else if (name.length > MAX_NAME_LENGTH) {
    fieldErrors.name = MESSAGE_BY_FIELD.name;
  }

  if (form.password.length < PASSWORD_MIN_LENGTH) {
    fieldErrors.password = `La contraseña tiene que tener al menos ${PASSWORD_MIN_LENGTH} caracteres.`;
  } else if (
    form.password.toLowerCase().includes(invitation.value.email.toLowerCase())
  ) {
    fieldErrors.password = "La contraseña no puede contener tu email.";
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
    return;
  }

  // The invitation email already has an account (someone else accepted first)
  if (err?.code === "EMAIL_ALREADY_EXISTS") {
    generalError.value = "Ya hay una cuenta con este email.";
    emailTaken.value = true;
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
  if (isLoading.value || authStore.isAuthenticated) return;

  clearErrors();
  authStore.clearError();

  if (!validate()) {
    await focusFirstError();
    return;
  }

  try {
    // The store keeps the user from the response (SessionResponse),
    // so there is no need to call /api/me afterwards.
    await authStore.acceptInvitation(code.value, {
      name: form.name.trim(),
      password: form.password,
      accept_terms: form.accept_terms,
    });

    // Success screen of the mockup; "Ir a mi panel" goes to CLIENT_HOME
    state.value = "done";
    await nextTick();
    doneHeading.value?.focus();
  } catch (err) {
    // Expired or used while the form was open: show the problem screen
    if (handleLinkError(err)) return;

    showApiError(err);
    await focusFirstError();
  }
}

async function logout() {
  await authStore.logout();
}

// Clear a field's error as soon as the user edits that field
for (const field of FIELD_ORDER) {
  watch(
    () => form[field],
    () => {
      fieldErrors[field] = "";
    },
  );
}

// Another link opened in the same tab (only the query changes): load it again
watch(code, () => {
  clearErrors();
  loadInvitation();
});

onMounted(async () => {
  authStore.clearError();
  // Find out if someone is already logged in, to show the log-out notice
  await authStore.initializeAuth();
  await loadInvitation();
});
</script>
