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
              :ref="link.setRef('link')"
              v-model="pastedLink"
              type="text"
              inputmode="url"
              autocomplete="off"
              spellcheck="false"
              :class="link.inputClass('link', 'font-mono text-sm')"
              v-bind="link.fieldAttrs('link')"
              placeholder="https://…/registro?invitacion=…"
            />
            <FieldError
              :id="link.errorId('link')"
              :message="link.errors.link"
            />
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

          <!-- novalidate: our own Spanish messages, the same in every form -->
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
                class="w-full px-4 py-3 border border-slate-200 rounded-lg bg-slate-100 text-slate-600 cursor-default focus:outline-none focus:ring-2 focus:ring-aqua-600"
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
                  :ref="setRef('password')"
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="new-password"
                  :class="inputClass('password', 'pr-20')"
                  v-bind="fieldAttrs('password', 'invite-password-hint')"
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
              <FieldError :id="errorId('password')" :message="errors.password" />
            </div>

            <!-- Terms and privacy -->
            <div>
              <div class="flex items-start gap-3">
                <input
                  id="invite-terms"
                  :ref="setRef('accept_terms')"
                  v-model="form.accept_terms"
                  type="checkbox"
                  class="mt-1 w-4 h-4 shrink-0 accent-aqua-600 cursor-pointer"
                  v-bind="fieldAttrs('accept_terms')"
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
              <FieldError
                :id="errorId('accept_terms')"
                :message="errors.accept_terms"
              />
            </div>

            <!-- General error (account exists, rate limit, network, unexpected) -->
            <FormError :message="generalError">
              <RouterLink
                v-if="emailTaken"
                to="/login"
                class="font-semibold underline hover:no-underline"
                >Entrar</RouterLink
              >
            </FormError>

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
import FieldError from "../../components/FieldError.vue";
import FormError from "../../components/FormError.vue";
import { useFieldErrors } from "../../composables/useFieldErrors.js";
import { apiErrorMessage } from "../../utils/apiError.js";
import { FIELD_LIMITS } from "../../utils/limits.js";
// Same rule as the backend (backend/app/shared/passwords.py), /prueba and Mi cuenta.
// The backend also rejects common passwords.
import {
  PASSWORD_MIN_LENGTH,
  passwordProblem,
} from "../../utils/passwords.js";
// Same name rule as /prueba and Mi cuenta (utils/validation.js)
import { cleanText, personNameProblem } from "../../utils/validation.js";

const TERMS_MESSAGE =
  "Tienes que aceptar los términos y la política de privacidad.";

// Where the new client lands. The session is already open: the accept
// response sets the cookie, as the register one does.
const CLIENT_HOME = "/dashboard";

// Shared classes, as in the mockup (pantallas/Invitacion.html)
const CARD =
  "bg-white border border-aqua-100 rounded-2xl p-6 sm:p-8 shadow-[0_16px_40px_theme(colors.aqua.600/10%)]";
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
} = useFieldErrors(["name", "password", "accept_terms"], { size: "lg" });
clearOnEdit({
  name: () => form.name,
  password: () => form.password,
  accept_terms: () => form.accept_terms,
});

const generalError = ref("");
const emailTaken = ref(false);
const showPassword = ref(false);

// "Sin código en la URL": the link (or bare code) the person pastes
const pastedLink = ref("");
const link = reactive(useFieldErrors(["link"], { size: "lg" }));
link.clearOnEdit({ link: () => pastedLink.value });

const problemHeading = ref(null);
const doneHeading = ref(null);

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

// API errors of one field. WEAK_PASSWORD and INVALID_NAME keep the backend
// message, which says exactly what is wrong
const API_ERRORS = {
  codes: {
    INVALID_NAME: "name",
    WEAK_PASSWORD: "password",
    TERMS_NOT_ACCEPTED: { field: "accept_terms", message: TERMS_MESSAGE },
  },
  messages: {
    name: `Escribe tu nombre (máximo ${FIELD_LIMITS.username} caracteres).`,
    password: "Revisa la contraseña.",
    accept_terms: TERMS_MESSAGE,
  },
};

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
  const valid = link.check({
    link: () =>
      pasted
        ? null
        : "No encontramos el código. Pega el enlace completo del email.",
  });
  if (!valid) {
    await link.focusFirstError();
    return;
  }
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
      err?.code === "TOO_MANY_REQUESTS"
        ? apiErrorMessage(err)
        : "Comprueba la conexión e inténtalo de nuevo.";
    state.value = "error";
  }
}

function retryLoad() {
  retried.value = true;
  loadInvitation();
}

function clearErrors() {
  clear();
  generalError.value = "";
  emailTaken.value = false;
}

async function handleSubmit() {
  if (isLoading.value || authStore.isAuthenticated) return;

  clearErrors();
  authStore.clearError();

  const valid = check({
    name: () => personNameProblem(form.name),
    password: () => passwordProblem(form.password, invitation.value.email),
    accept_terms: () => (form.accept_terms ? null : TERMS_MESSAGE),
  });
  if (!valid) {
    await focusFirstError();
    return;
  }

  try {
    // The store keeps the user from the response (SessionResponse),
    // so there is no need to call /api/me afterwards.
    await authStore.acceptInvitation(code.value, {
      name: cleanText(form.name),
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

    if (applyApiError(err, API_ERRORS)) {
      await focusFirstError();
      return;
    }
    // The invitation email already has an account (someone else accepted first)
    if (err?.code === "EMAIL_ALREADY_EXISTS") {
      generalError.value = "Ya hay una cuenta con este email.";
      emailTaken.value = true;
      return;
    }
    generalError.value = apiErrorMessage(
      err,
      "No hemos podido crear tu cuenta. Inténtalo de nuevo en unos minutos.",
    );
  }
}

async function logout() {
  await authStore.logout();
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
