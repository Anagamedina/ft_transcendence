<!--
  CLIENT SUBSCRIBE VIEW ("Hazte cliente", B14)
  A client on the free trial (running or expired) becomes a paying client.
  One page, five cards and a summary that stays in view on wide screens:
    1 Edificios y sensores: how many the client contracts, with the buildings
      it already has. The plan is not chosen: it is the smallest one that
      covers them (planFor), and the price is its base plus each sensor.
    2 Pago: monthly or yearly (ten months, two free).
    3 Datos de la empresa: legal name, tax id, phone, fiscal address.
    4 Facturación y pago: billing email and IBAN for SEPA direct debit.
    5 Condiciones: terms and privacy, and the SEPA authorization.
  Plans, prices and limits come from GET /api/plans. "Confirmar alta" sends
  POST /api/me/organization/subscribe and reloads /api/me, so the trial
  banner goes away. The API computes the plan and the price again; the
  checks here are the same as the backend ones, to show the errors before
  sending (the backend also checks the IBAN check digits).
-->

<template>
  <div class="mx-auto max-w-6xl space-y-6">
    <LoadingState v-if="loading" message="Cargando tu alta…" />

    <ErrorState v-else-if="loadError" :message="loadError" @retry="load" />

    <!-- Subscribed in this visit -->
    <section
      v-else-if="result"
      class="mx-auto max-w-xl rounded-2xl border border-slate-200 bg-white p-8 text-center"
      aria-labelledby="subscribe-done-title"
    >
      <h1
        id="subscribe-done-title"
        ref="doneTitle"
        tabindex="-1"
        class="font-serif text-3xl text-slate-900 focus:outline-none"
      >
        Ya eres <em class="text-aqua-600">cliente.</em>
      </h1>
      <p class="mt-3 text-slate-700">
        {{ result.organization_name }} tiene el plan {{ result.plan_name }} con
        {{ countText(result.contracted_sites, "edificio", "edificios") }} y
        {{ countText(result.contracted_sensors, "sensor", "sensores") }}:
        {{ euros(result.billed_price_eur) }}
        {{ result.billing_period === "YEARLY" ? "al año" : "al mes" }}, IVA no
        incluido. Lo cobraremos en la cuenta {{ result.iban_masked }}.
      </p>
      <RouterLink
        to="/app"
        class="mt-6 inline-block rounded-lg bg-aqua-600 px-5 py-3 font-semibold text-white hover:bg-aqua-700 focus:outline-none focus:ring-2 focus:ring-aqua-400"
      >
        Ir a mis edificios
      </RouterLink>
    </section>

    <!-- Not on the trial: nothing to subscribe to -->
    <section
      v-else-if="!isTrial"
      class="mx-auto max-w-xl rounded-2xl border border-slate-200 bg-white p-8"
      aria-labelledby="subscribe-not-trial-title"
    >
      <h1
        id="subscribe-not-trial-title"
        class="text-xl font-bold text-slate-900"
      >
        {{
          organization?.status === "ACTIVE"
            ? "Tu cuenta ya está activa"
            : "No puedes contratar un plan desde aquí"
        }}
      </h1>
      <p class="mt-2 text-slate-700">
        El alta solo se hace desde la prueba gratuita. Puedes ver el estado de
        tu cuenta en Mi cuenta.
      </p>
      <RouterLink
        to="/app/account"
        class="mt-4 inline-block font-semibold text-aqua-700 underline hover:text-aqua-900"
      >
        Ir a Mi cuenta
      </RouterLink>
    </section>

    <template v-else>
      <header>
        <p class="font-mono text-xs uppercase tracking-widest text-slate-500">
          {{ organization.name }} · {{ trialText }}
        </p>
        <h1 class="mt-2 font-serif text-4xl text-slate-900 md:text-5xl">
          Hazte <em class="text-aqua-600">cliente.</em>
        </h1>
        <p class="mt-3 max-w-2xl text-slate-700">
          Mantienes tus edificios, sus sensores y todo el histórico de la
          prueba. Solo necesitamos los datos para el contrato y la factura.
        </p>
      </header>

      <form
        class="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]"
        novalidate
        @submit.prevent="onSubmit"
      >
        <div class="space-y-6">
          <!-- 1. Edificios y sensores: what the client contracts -->
          <section :class="CARD_CLASS" aria-labelledby="subscribe-install">
            <h2 id="subscribe-install" :class="TITLE_CLASS">
              <span class="text-aqua-600">1</span> · Edificios y sensores
            </h2>
            <p class="-mt-3 mb-4 text-xs text-slate-600">
              Elige cuántos necesitas. El plan y el precio se calculan solos.
            </p>
            <div class="grid gap-4 sm:grid-cols-2">
              <div>
                <label for="subscribe-sites" :class="LABEL_CLASS">
                  Edificios
                </label>
                <input
                  id="subscribe-sites"
                  ref="sitesInput"
                  v-model.number="form.sites"
                  type="number"
                  inputmode="numeric"
                  :min="minSites"
                  :max="MAX_SITES"
                  step="1"
                  v-bind="fieldAttrs('sites')"
                  :aria-describedby="describedBy('sites')"
                />
                <p :id="hintId('sites')" class="mt-1 text-xs text-slate-600">
                  {{
                    sites.length > 0
                      ? `Ya tienes ${countText(sites.length, "edificio", "edificios")}.`
                      : `Entre 1 y ${MAX_SITES}.`
                  }}
                </p>
                <p
                  v-if="fieldErrors.sites"
                  :id="errorId('sites')"
                  :class="ERROR_CLASS"
                >
                  {{ fieldErrors.sites }}
                </p>
              </div>

              <div>
                <label for="subscribe-sensors" :class="LABEL_CLASS">
                  Sensores
                </label>
                <input
                  id="subscribe-sensors"
                  ref="sensorsInput"
                  v-model.number="form.sensors"
                  type="number"
                  inputmode="numeric"
                  :min="minSensors"
                  :max="MAX_SENSORS"
                  step="1"
                  v-bind="fieldAttrs('sensors')"
                  :aria-describedby="describedBy('sensors')"
                />
                <p :id="hintId('sensors')" class="mt-1 text-xs text-slate-600">
                  Uno por planta, contando sótanos.
                  <template v-if="recommendedSensors > 0">
                    En tus edificios: {{ recommendedSensors }}.
                  </template>
                  <template v-if="currentSensors > 0">
                    Ya tienes {{ currentSensors }}.
                  </template>
                </p>
                <p
                  v-if="fieldErrors.sensors"
                  :id="errorId('sensors')"
                  :class="ERROR_CLASS"
                >
                  {{ fieldErrors.sensors }}
                </p>
              </div>
            </div>

            <!-- The plan that covers them and how the price is made -->
            <div
              class="mt-5 rounded-xl border border-aqua-600 bg-aqua-50 p-4"
              aria-live="polite"
            >
              <template v-if="chosenPlan">
                <p class="font-semibold text-slate-900">
                  Plan {{ chosenPlan.name }}
                  <span class="font-normal text-slate-600">
                    · {{ chosenPlan.description }}
                  </span>
                </p>
                <p class="mt-1 font-mono text-sm text-slate-700">
                  {{ euros(chosenPlan.monthly_price_eur) }} +
                  {{ form.sensors }} × {{ euros(sensorPrice) }} =
                  <strong class="text-slate-900"
                    >{{ euros(monthlyTotal) }} / mes</strong
                  >
                </p>
              </template>
              <p v-else class="text-sm text-slate-700">
                Elige los edificios y sensores para ver el precio.
              </p>
            </div>

            <!-- Buildings from the trial: read only, only an admin edits them -->
            <div v-if="sites.length > 0" class="mt-5">
              <h3 class="text-sm font-semibold text-slate-900">
                Los que ya tienes
              </h3>
              <ul class="mt-2 divide-y divide-slate-200 text-sm text-slate-700">
                <li
                  v-for="site in sites"
                  :key="site.id"
                  class="flex flex-wrap justify-between gap-x-4 py-2"
                >
                  <span class="font-medium text-slate-900">{{
                    site.name
                  }}</span>
                  <span>{{ siteDetails(site) }}</span>
                </li>
              </ul>
            </div>
            <p class="mt-4 text-xs text-slate-600">
              Los edificios nuevos los damos de alta e instalamos sus sensores
              después del alta. ¿Dudas o más de {{ MAX_SITES }} edificios?
              <a
                :href="supportMailto"
                class="font-semibold text-aqua-700 underline hover:text-aqua-900"
                >Escríbenos a {{ SUPPORT_EMAIL }}</a
              >.
            </p>
          </section>

          <!-- 2. Pago: monthly or yearly -->
          <fieldset :class="CARD_CLASS">
            <legend class="sr-only">Pago</legend>
            <h2 :class="TITLE_CLASS" aria-hidden="true">
              <span class="text-aqua-600">2</span> · Pago
            </h2>
            <div class="grid gap-3 sm:grid-cols-2">
              <label
                v-for="option in periodOptions"
                :key="option.id"
                class="flex cursor-pointer gap-3 rounded-xl border p-4 transition focus-within:ring-2 focus-within:ring-aqua-400"
                :class="
                  form.period === option.id
                    ? 'border-aqua-600 bg-aqua-50'
                    : 'border-slate-300 hover:border-slate-400'
                "
              >
                <input
                  v-model="form.period"
                  type="radio"
                  name="period"
                  :value="option.id"
                  class="mt-1 accent-aqua-600"
                />
                <span>
                  <span class="block font-semibold text-slate-900">
                    {{ option.label }}
                  </span>
                  <span class="block text-sm text-slate-600">
                    {{ option.note }}
                  </span>
                  <span class="mt-2 block font-semibold text-slate-900">
                    {{ option.price }}
                  </span>
                </span>
              </label>
            </div>
          </fieldset>

          <!-- 2. Datos de la empresa -->
          <section :class="CARD_CLASS" aria-labelledby="subscribe-company">
            <h2 id="subscribe-company" :class="TITLE_CLASS">
              <span class="text-aqua-600">3</span> · Datos de la empresa
            </h2>
            <p class="-mt-3 mb-4 text-xs text-slate-600">
              Los que aparecerán en el contrato y en las facturas.
            </p>
            <div class="grid gap-4 sm:grid-cols-2">
              <div class="sm:col-span-2">
                <label for="subscribe-legal-name" :class="LABEL_CLASS">
                  Razón social
                </label>
                <input
                  id="subscribe-legal-name"
                  ref="legalNameInput"
                  v-model="form.legal_name"
                  type="text"
                  autocomplete="organization"
                  maxlength="200"
                  placeholder="p. ej. Hoteles del Turia, S.L."
                  v-bind="fieldAttrs('legal_name')"
                />
                <p
                  v-if="fieldErrors.legal_name"
                  :id="errorId('legal_name')"
                  :class="ERROR_CLASS"
                >
                  {{ fieldErrors.legal_name }}
                </p>
              </div>

              <div>
                <label for="subscribe-tax-id" :class="LABEL_CLASS">
                  CIF / NIF
                </label>
                <input
                  id="subscribe-tax-id"
                  ref="taxIdInput"
                  v-model="form.tax_id"
                  type="text"
                  autocapitalize="characters"
                  maxlength="30"
                  placeholder="B12345678"
                  v-bind="fieldAttrs('tax_id')"
                />
                <p
                  v-if="fieldErrors.tax_id"
                  :id="errorId('tax_id')"
                  :class="ERROR_CLASS"
                >
                  {{ fieldErrors.tax_id }}
                </p>
              </div>

              <div>
                <label for="subscribe-phone" :class="LABEL_CLASS">
                  Teléfono de la empresa
                  <span class="font-normal text-slate-500">(opcional)</span>
                </label>
                <input
                  id="subscribe-phone"
                  ref="phoneInput"
                  v-model="form.phone"
                  type="tel"
                  autocomplete="tel"
                  maxlength="30"
                  v-bind="fieldAttrs('phone')"
                />
                <p
                  v-if="fieldErrors.phone"
                  :id="errorId('phone')"
                  :class="ERROR_CLASS"
                >
                  {{ fieldErrors.phone }}
                </p>
              </div>

              <div class="sm:col-span-2">
                <label for="subscribe-address" :class="LABEL_CLASS">
                  Dirección fiscal
                </label>
                <input
                  id="subscribe-address"
                  ref="addressInput"
                  v-model="form.address"
                  type="text"
                  autocomplete="street-address"
                  :maxlength="ADDRESS_MAX_LENGTH"
                  v-bind="fieldAttrs('address')"
                />
                <p
                  v-if="fieldErrors.address"
                  :id="errorId('address')"
                  :class="ERROR_CLASS"
                >
                  {{ fieldErrors.address }}
                </p>
              </div>

              <div>
                <label for="subscribe-postal-code" :class="LABEL_CLASS">
                  Código postal
                </label>
                <input
                  id="subscribe-postal-code"
                  ref="postalCodeInput"
                  v-model="form.postal_code"
                  type="text"
                  inputmode="numeric"
                  autocomplete="postal-code"
                  maxlength="5"
                  v-bind="fieldAttrs('postal_code')"
                />
                <p
                  v-if="fieldErrors.postal_code"
                  :id="errorId('postal_code')"
                  :class="ERROR_CLASS"
                >
                  {{ fieldErrors.postal_code }}
                </p>
              </div>

              <div>
                <label for="subscribe-city" :class="LABEL_CLASS">
                  Ciudad y provincia
                </label>
                <input
                  id="subscribe-city"
                  ref="cityInput"
                  v-model="form.city"
                  type="text"
                  autocomplete="address-level2"
                  maxlength="120"
                  v-bind="fieldAttrs('city')"
                />
                <p
                  v-if="fieldErrors.city"
                  :id="errorId('city')"
                  :class="ERROR_CLASS"
                >
                  {{ fieldErrors.city }}
                </p>
              </div>
            </div>
          </section>

          <!-- 3. Facturación y pago -->
          <section :class="CARD_CLASS" aria-labelledby="subscribe-billing">
            <h2 id="subscribe-billing" :class="TITLE_CLASS">
              <span class="text-aqua-600">4</span> · Facturación y pago
            </h2>
            <div class="grid gap-4">
              <div>
                <label for="subscribe-billing-email" :class="LABEL_CLASS">
                  Email para las facturas
                </label>
                <input
                  id="subscribe-billing-email"
                  ref="billingEmailInput"
                  v-model="form.billing_email"
                  type="email"
                  autocomplete="email"
                  maxlength="320"
                  v-bind="fieldAttrs('billing_email')"
                />
                <p
                  v-if="fieldErrors.billing_email"
                  :id="errorId('billing_email')"
                  :class="ERROR_CLASS"
                >
                  {{ fieldErrors.billing_email }}
                </p>
              </div>

              <div>
                <label for="subscribe-iban" :class="LABEL_CLASS">
                  IBAN para la domiciliación
                </label>
                <input
                  id="subscribe-iban"
                  ref="ibanInput"
                  v-model="form.iban"
                  type="text"
                  autocomplete="off"
                  autocapitalize="characters"
                  maxlength="42"
                  placeholder="ES00 0000 0000 0000 0000 0000"
                  v-bind="fieldAttrs('iban', 'font-mono')"
                />
                <p
                  v-if="fieldErrors.iban"
                  :id="errorId('iban')"
                  :class="ERROR_CLASS"
                >
                  {{ fieldErrors.iban }}
                </p>
                <p class="mt-1 text-xs text-slate-600">
                  Cobro {{ chosenPeriod.everyText }} por domiciliación SEPA. No
                  guardamos tarjetas y solo guardamos el IBAN enmascarado.
                </p>
              </div>
            </div>
          </section>

          <!-- 5. Condiciones -->
          <fieldset :class="CARD_CLASS">
            <legend class="sr-only">Condiciones</legend>
            <h2 :class="TITLE_CLASS" aria-hidden="true">
              <span class="text-aqua-600">5</span> · Condiciones
            </h2>
            <div class="space-y-3">
              <div>
                <div class="flex items-start gap-3">
                  <input
                    id="subscribe-terms"
                    ref="termsInput"
                    v-model="form.accept_terms"
                    type="checkbox"
                    class="mt-1 h-4 w-4 accent-aqua-600"
                    :aria-invalid="Boolean(fieldErrors.accept_terms)"
                    :aria-describedby="
                      fieldErrors.accept_terms
                        ? errorId('accept_terms')
                        : undefined
                    "
                  />
                  <label for="subscribe-terms" class="text-sm text-slate-700">
                    Acepto las
                    <a
                      href="/legal#terminos"
                      target="_blank"
                      rel="noopener"
                      class="text-aqua-700 underline hover:text-aqua-900"
                      >condiciones del servicio</a
                    >
                    y la
                    <a
                      href="/legal#privacidad"
                      target="_blank"
                      rel="noopener"
                      class="text-aqua-700 underline hover:text-aqua-900"
                      >Política de privacidad</a
                    >. <span class="text-slate-500">Obligatorio.</span>
                  </label>
                </div>
                <p
                  v-if="fieldErrors.accept_terms"
                  :id="errorId('accept_terms')"
                  :class="ERROR_CLASS"
                >
                  {{ fieldErrors.accept_terms }}
                </p>
              </div>

              <div>
                <div class="flex items-start gap-3">
                  <input
                    id="subscribe-sepa"
                    ref="sepaInput"
                    v-model="form.accept_sepa"
                    type="checkbox"
                    class="mt-1 h-4 w-4 accent-aqua-600"
                    :aria-invalid="Boolean(fieldErrors.accept_sepa)"
                    :aria-describedby="
                      fieldErrors.accept_sepa
                        ? errorId('accept_sepa')
                        : undefined
                    "
                  />
                  <label for="subscribe-sepa" class="text-sm text-slate-700">
                    Autorizo la domiciliación SEPA en la cuenta indicada.
                    <span class="text-slate-500"
                      >Obligatorio para pagar por domiciliación.</span
                    >
                  </label>
                </div>
                <p
                  v-if="fieldErrors.accept_sepa"
                  :id="errorId('accept_sepa')"
                  :class="ERROR_CLASS"
                >
                  {{ fieldErrors.accept_sepa }}
                </p>
              </div>
            </div>
          </fieldset>
        </div>

        <!-- Summary: stays in view while the form scrolls on wide screens -->
        <aside
          class="rounded-2xl border border-slate-200 bg-white p-6 lg:sticky lg:top-6"
          aria-labelledby="subscribe-summary"
        >
          <h2 id="subscribe-summary" class="font-serif text-2xl text-slate-900">
            Resumen
          </h2>
          <dl class="mt-4 space-y-2 text-sm">
            <div
              v-for="row in summaryRows"
              :key="row.label"
              class="flex justify-between gap-4"
            >
              <dt class="text-slate-600">{{ row.label }}</dt>
              <dd class="text-right font-medium text-slate-900">
                {{ row.value }}
              </dd>
            </div>
          </dl>
          <div
            class="mt-4 flex items-baseline justify-between gap-4 border-t border-slate-200 pt-4"
          >
            <span class="text-sm text-slate-600">Total</span>
            <span class="text-2xl font-bold text-slate-900">
              {{ chosenPeriod.price }}
            </span>
          </div>
          <p class="mt-1 text-right text-xs text-slate-500">IVA no incluido</p>

          <p
            v-if="generalError"
            class="mt-4 rounded-lg border border-danger bg-danger-light/40 p-3 text-sm text-slate-900"
            role="alert"
          >
            {{ generalError }}
          </p>

          <button
            type="submit"
            class="mt-4 w-full rounded-full bg-aqua-600 px-5 py-3 font-semibold text-white hover:bg-aqua-700 focus:outline-none focus:ring-2 focus:ring-aqua-400 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="submitting"
          >
            {{ submitting ? "Dando de alta…" : "Confirmar alta" }}
          </button>
          <p class="mt-3 text-xs text-slate-600">
            Puedes pedir la baja cuando quieras desde Mi cuenta.
          </p>
        </aside>
      </form>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from "vue";
import LoadingState from "../../components/LoadingState.vue";
import ErrorState from "../../components/ErrorState.vue";
import subscriptionsService from "../../services/subscriptions.service.js";
import { useAuthStore } from "../../stores/auth";
import { useSitesStore } from "../../stores/sites";
import { parseDate } from "../../composables/useFormat";
import { apiErrorMessage } from "../../utils/apiError";
import { billedPrice, monthlyPrice, planFor } from "../../utils/pricing";

// Where clients ask about the contract (no in-app request yet)
const SUPPORT_EMAIL = "soporte@aquaguard.dev";

// Same limits as SubscriptionRequest (subscriptions/schemas.py)
const MAX_SITES = 100;
const MAX_SENSORS = 1000;

const ADDRESS_MAX_LENGTH = 200;
const DAY_MS = 24 * 60 * 60 * 1000;

// Same checks as the backend (subscriptions/service.py)
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const POSTAL_CODE_PATTERN = /^\d{5}$/;
const SEPARATORS = /[\s.-]/g;
const TAX_ID_PATTERN = /^[A-Z0-9]{8,15}$/;
const IBAN_PATTERN = /^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$/;

const CARD_CLASS = "rounded-2xl border border-slate-200 bg-white p-6";
const TITLE_CLASS = "mb-4 font-bold text-slate-900";
const LABEL_CLASS = "mb-1 block text-xs font-semibold text-slate-700";
const ERROR_CLASS = "mt-1 text-sm text-danger";
const INPUT_CLASS =
  "w-full rounded-lg border px-4 py-3 focus:outline-none focus:ring-2 focus:ring-aqua-400";

const authStore = useAuthStore();
const sitesStore = useSitesStore();

const organization = computed(() => authStore.organization);
const isTrial = computed(() => organization.value?.status === "TRIAL");
const sites = computed(() => sitesStore.sites);

// GET /api/plans, from the smallest to the largest
const plans = ref([]);
const loading = ref(true);
const loadError = ref("");
const submitting = ref(false);
const generalError = ref("");
const result = ref(null);
const doneTitle = ref(null);

const form = reactive({
  // Filled in by load(), from the buildings the client already has
  sites: 1,
  sensors: 1,
  period: "MONTHLY",
  legal_name: "",
  tax_id: "",
  phone: "",
  address: "",
  postal_code: "",
  city: "",
  billing_email: authStore.user?.email ?? "",
  iban: "",
  accept_terms: false,
  accept_sepa: false,
});

// Fields in screen order: the first one with an error gets the focus
const FIELD_ORDER = [
  "sites",
  "sensors",
  "legal_name",
  "tax_id",
  "phone",
  "address",
  "postal_code",
  "city",
  "billing_email",
  "iban",
  "accept_terms",
  "accept_sepa",
];

const fieldErrors = reactive(
  Object.fromEntries(FIELD_ORDER.map((field) => [field, ""])),
);

// Template refs, to move the focus to the first field with an error
const sitesInput = ref(null);
const sensorsInput = ref(null);
const legalNameInput = ref(null);
const taxIdInput = ref(null);
const phoneInput = ref(null);
const addressInput = ref(null);
const postalCodeInput = ref(null);
const cityInput = ref(null);
const billingEmailInput = ref(null);
const ibanInput = ref(null);
const termsInput = ref(null);
const sepaInput = ref(null);

const inputRefs = {
  sites: sitesInput,
  sensors: sensorsInput,
  legal_name: legalNameInput,
  tax_id: taxIdInput,
  phone: phoneInput,
  address: addressInput,
  postal_code: postalCodeInput,
  city: cityInput,
  billing_email: billingEmailInput,
  iban: ibanInput,
  accept_terms: termsInput,
  accept_sepa: sepaInput,
};

// API field names that are not the field on screen
const SCREEN_FIELD_BY_API_FIELD = { billing_address: "address" };

// Backend error codes that belong to one field, with our Spanish text
const FIELD_BY_CODE = {
  SENSORS_BELOW_SITES: "sensors",
  INVALID_TAX_ID: "tax_id",
  INVALID_POSTAL_CODE: "postal_code",
  INVALID_IBAN: "iban",
  TERMS_NOT_ACCEPTED: "accept_terms",
  SEPA_NOT_ACCEPTED: "accept_sepa",
};

// The backend checks more than the shape (the IBAN check digits), so its
// rejection gets its own text instead of the shape hint of MESSAGE_BY_FIELD
const MESSAGE_BY_CODE = {
  SENSORS_BELOW_SITES: "Necesitas al menos un sensor por edificio.",
  INVALID_IBAN: "El IBAN no es válido: revisa los dígitos de la cuenta.",
};

const MESSAGE_BY_FIELD = {
  sites: `Elige entre 1 y ${MAX_SITES} edificios.`,
  sensors: `Elige entre 1 y ${MAX_SENSORS} sensores.`,
  legal_name: "Escribe la razón social (máximo 200 caracteres).",
  tax_id: "Escribe un CIF o NIF válido: entre 8 y 15 letras o números.",
  phone: "Escribe un teléfono de 30 caracteres como máximo.",
  address: "Escribe la dirección fiscal.",
  postal_code: "Escribe un código postal de 5 cifras.",
  city: "Escribe la ciudad y la provincia (máximo 120 caracteres).",
  billing_email: "Escribe un email válido, por ejemplo facturas@empresa.com.",
  iban: "Revisa el IBAN: empieza por el país (ES) y tiene 24 caracteres en España.",
  accept_terms:
    "Tienes que aceptar las condiciones y la política de privacidad.",
  accept_sepa: "Tienes que autorizar la domiciliación para pagar por SEPA.",
};

function euros(value) {
  return `${new Intl.NumberFormat("es-ES").format(value)} €`;
}

function countText(count, one, many) {
  return `${count} ${count === 1 ? one : many}`;
}

// What the client already has: it cannot contract less
const currentSensors = computed(() =>
  sites.value.reduce((total, site) => total + (site.sensor_count ?? 0), 0),
);
const minSites = computed(() => Math.max(1, sites.value.length));
const minSensors = computed(() =>
  Math.max(1, currentSensors.value, Number(form.sites) || 1),
);

// One sensor per floor, basements included, as in the price table
const recommendedSensors = computed(() =>
  sites.value.reduce(
    (total, site) => total + (site.floors ?? 0) + (site.basements ?? 0),
    0,
  ),
);

function isWhole(value, min, max) {
  return Number.isInteger(value) && value >= min && value <= max;
}

const contractValid = computed(
  () =>
    isWhole(form.sites, minSites.value, MAX_SITES) &&
    isWhole(form.sensors, minSensors.value, MAX_SENSORS),
);

// Plan and price with the same rules as the API (utils/pricing.js)
const chosenPlan = computed(() =>
  contractValid.value ? planFor(plans.value, form.sites, form.sensors) : null,
);

const sensorPrice = computed(() => plans.value[0]?.sensor_price_eur ?? 0);

const monthlyTotal = computed(() =>
  chosenPlan.value ? monthlyPrice(chosenPlan.value, form.sensors) : 0,
);

const periodOptions = computed(() => {
  const free = 12 - (plans.value[0]?.yearly_months ?? 12);
  return [
    {
      id: "MONTHLY",
      label: "Mensual",
      note: "Sin permanencia",
      price: chosenPlan.value ? `${euros(monthlyTotal.value)} / mes` : "—",
      everyText: "mensual",
    },
    {
      id: "YEARLY",
      label: "Anual",
      note: free === 1 ? "Un mes gratis" : `${free} meses gratis`,
      price: chosenPlan.value
        ? `${euros(billedPrice(chosenPlan.value, form.sensors, "YEARLY"))} / año`
        : "—",
      everyText: "anual",
    },
  ];
});

const chosenPeriod = computed(() =>
  periodOptions.value.find((option) => option.id === form.period),
);

const trialEnd = computed(() => parseDate(organization.value?.trial_ends_at));
const trialExpired = computed(
  () => !trialEnd.value || trialEnd.value <= new Date(),
);

// Calendar days left, the same count as TrialBanner
const daysLeft = computed(() => {
  if (!trialEnd.value) return 0;
  const today = new Date();
  const end = new Date(trialEnd.value);
  today.setHours(0, 0, 0, 0);
  end.setHours(0, 0, 0, 0);
  return Math.max(0, Math.round((end - today) / DAY_MS));
});

const trialText = computed(() => {
  if (trialExpired.value) return "tu prueba ha terminado";
  if (daysLeft.value > 1) return `te quedan ${daysLeft.value} días de prueba`;
  if (daysLeft.value === 1) return "te queda 1 día de prueba";
  return "tu prueba termina hoy";
});

const listFormat = new Intl.ListFormat("es", {
  style: "long",
  type: "conjunction",
});
const siteNames = computed(() =>
  listFormat.format(sites.value.map((site) => site.name)),
);

// Email with the subject and the client's current buildings already written
const supportMailto = computed(() => {
  const name = organization.value?.name ?? "";
  const subject = `Alta de ${name} en AquaGuard`;
  const body = [
    "Hola:",
    "",
    `Somos ${name} y queremos contratar AquaGuard.`,
    `Ahora tenemos ${countText(sites.value.length, "edificio", "edificios")}: ${siteNames.value || "ninguno"}.`,
    "",
    "Nuestra consulta:",
    "",
  ].join("\n");
  return `mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
});

function siteDetails(site) {
  const floors = countText(site.floors ?? 1, "planta", "plantas");
  const basements = site.basements
    ? ` y ${countText(site.basements, "sótano", "sótanos")}`
    : "";
  const sensors = countText(site.sensor_count ?? 0, "sensor", "sensores");
  return `${floors}${basements} · ${sensors}`;
}

const summaryRows = computed(() => [
  { label: "Plan", value: chosenPlan.value?.name ?? "—" },
  { label: "Pago", value: chosenPeriod.value.label },
  {
    label: "Edificios",
    value: Number.isInteger(form.sites) ? String(form.sites) : "—",
  },
  {
    label: "Sensores",
    value: Number.isInteger(form.sensors) ? String(form.sensors) : "—",
  },
  {
    label: "Precio al mes",
    value: chosenPlan.value ? euros(monthlyTotal.value) : "—",
  },
  // The API activates the account when it gets the request, not when the trial ends
  { label: "Empieza", value: "hoy, al confirmar el alta" },
]);

function errorId(field) {
  return `subscribe-${field}-error`;
}

function hintId(field) {
  return `subscribe-${field}-hint`;
}

// Hint always, and the error when there is one
function describedBy(field) {
  return [hintId(field), fieldErrors[field] ? errorId(field) : null]
    .filter(Boolean)
    .join(" ");
}

// Class and aria attributes of a text input, marked when it has an error
function fieldAttrs(field, extraClass = "") {
  const hasError = Boolean(fieldErrors[field]);
  return {
    class: [
      INPUT_CLASS,
      extraClass,
      hasError ? "border-danger bg-danger-light/40" : "border-slate-300",
    ],
    "aria-invalid": hasError,
    "aria-describedby": hasError ? errorId(field) : undefined,
  };
}

function clearErrors() {
  for (const field of FIELD_ORDER) fieldErrors[field] = "";
  generalError.value = "";
}

function compact(value) {
  return value.replace(SEPARATORS, "").toUpperCase();
}

// The same rules as the API, with the reason of the first one that fails
function sitesError() {
  if (!isWhole(form.sites, 1, MAX_SITES)) return MESSAGE_BY_FIELD.sites;
  if (form.sites < sites.value.length) {
    return `Ya tienes ${sites.value.length} edificios: contrata al menos ${sites.value.length}.`;
  }
  return "";
}

function sensorsError() {
  if (!isWhole(form.sensors, 1, MAX_SENSORS)) return MESSAGE_BY_FIELD.sensors;
  if (Number.isInteger(form.sites) && form.sensors < form.sites) {
    return `Necesitas al menos un sensor por edificio: ${form.sites}.`;
  }
  if (form.sensors < currentSensors.value) {
    return `Ya tienes ${currentSensors.value} sensores: contrata al menos ${currentSensors.value}.`;
  }
  return "";
}

// Client-side checks, before calling the API. Returns true when valid.
function validate() {
  fieldErrors.sites = sitesError();
  fieldErrors.sensors = sensorsError();
  if (!form.legal_name.trim())
    fieldErrors.legal_name = MESSAGE_BY_FIELD.legal_name;
  if (!TAX_ID_PATTERN.test(compact(form.tax_id))) {
    fieldErrors.tax_id = MESSAGE_BY_FIELD.tax_id;
  }
  if (form.phone.trim().length > 30) fieldErrors.phone = MESSAGE_BY_FIELD.phone;
  if (!form.address.trim()) fieldErrors.address = MESSAGE_BY_FIELD.address;
  if (!POSTAL_CODE_PATTERN.test(form.postal_code.trim())) {
    fieldErrors.postal_code = MESSAGE_BY_FIELD.postal_code;
  }
  if (!form.city.trim()) fieldErrors.city = MESSAGE_BY_FIELD.city;
  if (!EMAIL_PATTERN.test(form.billing_email.trim())) {
    fieldErrors.billing_email = MESSAGE_BY_FIELD.billing_email;
  }
  if (!IBAN_PATTERN.test(compact(form.iban))) {
    fieldErrors.iban = MESSAGE_BY_FIELD.iban;
  }
  if (!form.accept_terms)
    fieldErrors.accept_terms = MESSAGE_BY_FIELD.accept_terms;
  if (!form.accept_sepa) fieldErrors.accept_sepa = MESSAGE_BY_FIELD.accept_sepa;

  return FIELD_ORDER.every((field) => !fieldErrors[field]);
}

function focusFirstError() {
  const field = FIELD_ORDER.find((name) => fieldErrors[name]);
  if (field) inputRefs[field].value?.focus();
}

function toPayload() {
  const phone = form.phone.trim();
  return {
    sites: form.sites,
    sensors: form.sensors,
    billing_period: form.period,
    legal_name: form.legal_name.trim(),
    tax_id: form.tax_id.trim(),
    billing_address: form.address.trim(),
    postal_code: form.postal_code.trim(),
    city: form.city.trim(),
    billing_email: form.billing_email.trim(),
    phone: phone || null,
    iban: form.iban.trim(),
    accept_terms: form.accept_terms,
    accept_sepa: form.accept_sepa,
  };
}

// Turns an API error (already normalized by the adapter) into field or general messages
async function showApiError(err) {
  const field = FIELD_BY_CODE[err?.code];
  if (field) {
    fieldErrors[field] = MESSAGE_BY_CODE[err.code] ?? MESSAGE_BY_FIELD[field];
    return;
  }

  // Less than what it already has (a building or sensor was added meanwhile):
  // the API says which field and how many. Reload the buildings for the minimums.
  if (err?.code === "CONTRACT_BELOW_CURRENT") {
    const apiField = err.details?.[0]?.field;
    if (apiField in fieldErrors) {
      fieldErrors[apiField] = err.message;
      await sitesStore.fetchSites().catch(() => {});
      return;
    }
  }

  // Generic 422: details = [{ field, message, type }]
  if (err?.code === "VALIDATION_ERROR" && Array.isArray(err.details)) {
    let matched = false;
    for (const detail of err.details) {
      const screenField =
        SCREEN_FIELD_BY_API_FIELD[detail?.field] ?? detail?.field;
      if (screenField in fieldErrors) {
        fieldErrors[screenField] = MESSAGE_BY_FIELD[screenField];
        matched = true;
      }
    }
    if (matched) return;
  }

  // Already a client (another tab, or an admin activated it): reload the session
  if (err?.code === "ORGANIZATION_NOT_IN_TRIAL") {
    await authStore.fetchMe();
    return;
  }

  generalError.value = apiErrorMessage(
    err,
    "No hemos podido completar el alta. Inténtalo de nuevo en unos minutos.",
  );
}

async function onSubmit() {
  if (submitting.value) return;
  clearErrors();
  if (!validate()) {
    await nextTick();
    focusFirstError();
    return;
  }

  submitting.value = true;
  try {
    const response = await subscriptionsService.subscribe(toPayload());
    result.value = response.data;
    // The organization is ACTIVE now: the trial banner and the read-only mode go away
    await authStore.fetchMe();
    await nextTick();
    doneTitle.value?.focus();
  } catch (err) {
    await showApiError(err);
    await nextTick();
    focusFirstError();
  } finally {
    submitting.value = false;
  }
}

async function load() {
  loading.value = true;
  loadError.value = "";
  try {
    const [plansResponse] = await Promise.all([
      subscriptionsService.getPlans(),
      sitesStore.fetchSites(),
    ]);
    plans.value = plansResponse.data;
    if (plans.value.length === 0) {
      loadError.value = "Los planes no están disponibles ahora mismo.";
    }
    // Start from what the client has: its buildings, one sensor per floor
    form.sites = minSites.value;
    form.sensors = Math.max(minSensors.value, recommendedSensors.value);
  } catch (err) {
    loadError.value = apiErrorMessage(
      err,
      "No hemos podido cargar los datos del alta.",
    );
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>
