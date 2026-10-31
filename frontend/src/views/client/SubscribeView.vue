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
          Nos alegra que te quedes. Conservas todo lo de la prueba.
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
            <div class="grid gap-4 sm:grid-cols-2">
              <div>
                <label for="subscribe-sites" :class="LABEL_CLASS">
                  Edificios
                </label>
                <input
                  id="subscribe-sites"
                  :ref="setRef('sites')"
                  v-model.number="form.sites"
                  type="number"
                  inputmode="numeric"
                  :min="minSites"
                  :max="MAX_SITES"
                  step="1"
                  :class="inputClass('sites')"
                  v-bind="fieldAttrs('sites')"
                />
                <FieldError :id="errorId('sites')" :message="errors.sites" />
              </div>

              <div>
                <label for="subscribe-sensors" :class="LABEL_CLASS">
                  Sensores
                </label>
                <input
                  id="subscribe-sensors"
                  :ref="setRef('sensors')"
                  v-model.number="form.sensors"
                  type="number"
                  inputmode="numeric"
                  :min="minSensors"
                  :max="MAX_SENSORS"
                  step="1"
                  :class="inputClass('sensors')"
                  v-bind="fieldAttrs('sensors', hintId('sensors'))"
                />
                <p :id="hintId('sensors')" class="mt-1 text-xs text-slate-600">
                  Uno por planta, contando sótanos.
                </p>
                <FieldError :id="errorId('sensors')" :message="errors.sensors" />
              </div>
            </div>

            <!-- More than the biggest plan: a custom quote -->
            <p
              v-if="form.sites > MAX_SITES"
              class="mt-5 rounded-xl border border-aqua-600 bg-aqua-50 p-4 text-sm text-slate-700"
              aria-live="polite"
            >
              Más de {{ MAX_SITES }} edificios es un presupuesto a medida:
              <a
                :href="supportMailto"
                class="font-semibold text-aqua-700 underline hover:text-aqua-900"
                >escríbenos</a
              >.
            </p>

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
              ¿Más de {{ MAX_SITES }} edificios?
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
                    <span
                      v-if="chosenPlan"
                      class="text-xs font-normal text-slate-500"
                      >+ IVA</span
                    >
                  </span>
                </span>
              </label>
            </div>
          </fieldset>

          <!-- 3. Datos de la empresa -->
          <section :class="CARD_CLASS" aria-labelledby="subscribe-company">
            <h2 id="subscribe-company" :class="TITLE_CLASS">
              <span class="text-aqua-600">3</span> · Datos de la empresa
            </h2>
            <div class="grid gap-4 sm:grid-cols-2">
              <div class="sm:col-span-2">
                <label for="subscribe-legal-name" :class="LABEL_CLASS">
                  Razón social
                </label>
                <input
                  id="subscribe-legal-name"
                  :ref="setRef('legal_name')"
                  v-model="form.legal_name"
                  type="text"
                  autocomplete="organization"
                  maxlength="200"
                  placeholder="p. ej. Hoteles del Turia, S.L."
                  :class="inputClass('legal_name')"
                  v-bind="fieldAttrs('legal_name')"
                />
                <FieldError :id="errorId('legal_name')" :message="errors.legal_name" />
              </div>

              <div>
                <label for="subscribe-tax-id" :class="LABEL_CLASS">
                  CIF / NIF
                </label>
                <input
                  id="subscribe-tax-id"
                  :ref="setRef('tax_id')"
                  v-model="form.tax_id"
                  type="text"
                  autocapitalize="characters"
                  maxlength="30"
                  placeholder="B12345678"
                  :class="inputClass('tax_id')"
                  v-bind="fieldAttrs('tax_id')"
                />
                <FieldError :id="errorId('tax_id')" :message="errors.tax_id" />
              </div>

              <div>
                <label for="subscribe-phone" :class="LABEL_CLASS">
                  Teléfono de la empresa
                </label>
                <input
                  id="subscribe-phone"
                  :ref="setRef('phone')"
                  v-model="form.phone"
                  type="tel"
                  autocomplete="tel"
                  maxlength="30"
                  :class="inputClass('phone')"
                  v-bind="fieldAttrs('phone')"
                />
                <FieldError :id="errorId('phone')" :message="errors.phone" />
              </div>

              <div class="sm:col-span-2">
                <label for="subscribe-address" :class="LABEL_CLASS">
                  Dirección fiscal
                </label>
                <input
                  id="subscribe-address"
                  :ref="setRef('address')"
                  v-model="form.address"
                  type="text"
                  autocomplete="street-address"
                  :maxlength="ADDRESS_MAX_LENGTH"
                  :class="inputClass('address')"
                  v-bind="fieldAttrs('address')"
                />
                <FieldError :id="errorId('address')" :message="errors.address" />
              </div>

              <div>
                <label for="subscribe-postal-code" :class="LABEL_CLASS">
                  Código postal
                </label>
                <input
                  id="subscribe-postal-code"
                  :ref="setRef('postal_code')"
                  v-model="form.postal_code"
                  type="text"
                  inputmode="numeric"
                  autocomplete="postal-code"
                  maxlength="5"
                  :class="inputClass('postal_code')"
                  v-bind="fieldAttrs('postal_code')"
                />
                <FieldError :id="errorId('postal_code')" :message="errors.postal_code" />
              </div>

              <div>
                <label for="subscribe-city" :class="LABEL_CLASS">
                  Ciudad y provincia
                </label>
                <input
                  id="subscribe-city"
                  :ref="setRef('city')"
                  v-model="form.city"
                  type="text"
                  autocomplete="address-level2"
                  maxlength="120"
                  :class="inputClass('city')"
                  v-bind="fieldAttrs('city')"
                />
                <FieldError :id="errorId('city')" :message="errors.city" />
              </div>
            </div>
          </section>

          <!-- 4. Facturación y pago -->
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
                  :ref="setRef('billing_email')"
                  v-model="form.billing_email"
                  type="email"
                  autocomplete="email"
                  maxlength="320"
                  :class="inputClass('billing_email')"
                  v-bind="fieldAttrs('billing_email')"
                />
                <FieldError :id="errorId('billing_email')" :message="errors.billing_email" />
              </div>

              <div>
                <label for="subscribe-iban" :class="LABEL_CLASS">
                  IBAN para la domiciliación
                </label>
                <input
                  id="subscribe-iban"
                  :ref="setRef('iban')"
                  v-model="form.iban"
                  type="text"
                  autocomplete="off"
                  autocapitalize="characters"
                  maxlength="42"
                  placeholder="ES00 0000 0000 0000 0000 0000"
                  :class="inputClass('iban', 'font-mono')"
                  v-bind="fieldAttrs('iban')"
                />
                <FieldError :id="errorId('iban')" :message="errors.iban" />
                <p class="mt-1 text-xs text-slate-600">
                  Solo guardamos el IBAN enmascarado.
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
                    :ref="setRef('accept_terms')"
                    v-model="form.accept_terms"
                    type="checkbox"
                    class="mt-1 h-4 w-4 accent-aqua-600"
                    v-bind="fieldAttrs('accept_terms')"
                  />
                  <label for="subscribe-terms" class="text-sm text-slate-700">
                    Acepto las
                    <a
                      href="/legal#terminos-contratacion"
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
                    >.
                  </label>
                </div>
                <FieldError :id="errorId('accept_terms')" :message="errors.accept_terms" />
              </div>

              <div>
                <div class="flex items-start gap-3">
                  <input
                    id="subscribe-sepa"
                    :ref="setRef('accept_sepa')"
                    v-model="form.accept_sepa"
                    type="checkbox"
                    class="mt-1 h-4 w-4 accent-aqua-600"
                    v-bind="fieldAttrs('accept_sepa')"
                  />
                  <label for="subscribe-sepa" class="text-sm text-slate-700">
                    Autorizo la domiciliación SEPA en la cuenta indicada.
                  </label>
                </div>
                <FieldError :id="errorId('accept_sepa')" :message="errors.accept_sepa" />
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
              {{ totalWithVat || chosenPeriod.price }}
            </span>
          </div>
          <p class="mt-1 text-right text-xs text-slate-500">
            IVA ({{ VAT_PERCENT }} %) incluido
          </p>
          <p v-if="totalWithVat" class="text-right text-xs text-slate-500">
            Sin IVA: {{ chosenPeriod.price }}
          </p>

          <FormError class="mt-4" :message="generalError" />

          <button
            type="submit"
            class="mt-4 w-full rounded-full bg-aqua-600 px-5 py-3 font-semibold text-white hover:bg-aqua-700 focus:outline-none focus:ring-2 focus:ring-aqua-400 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="submitting"
          >
            {{ submitting ? "Dando de alta…" : "Confirmar alta" }}
          </button>
        </aside>
      </form>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import LoadingState from "../../components/LoadingState.vue";
import ErrorState from "../../components/ErrorState.vue";
import subscriptionsService from "../../services/subscriptions.service.js";
import { useAuthStore } from "../../stores/auth";
import { useSitesStore } from "../../stores/sites";
import { parseDate } from "../../composables/useFormat";
import { apiErrorMessage } from "../../utils/apiError";
import { billedPrice, monthlyPrice, planFor } from "../../utils/pricing";
import FieldError from "../../components/FieldError.vue";
import FormError from "../../components/FormError.vue";
import { useFieldErrors } from "../../composables/useFieldErrors.js";
// Same rules as the API and the new client wizard (utils/validation.js)
import {
  cleanText,
  emailProblem,
  ibanProblem,
  phoneProblem,
  postalCodeProblem,
  taxIdProblem,
  textProblem,
} from "../../utils/validation";

// Where clients ask about the contract (no in-app request yet)
const SUPPORT_EMAIL = "soporte@aquaguard.dev";

// Same limits as SubscriptionRequest (subscriptions/schemas.py). Buildings:
// the most the Empresa plan covers; more is a custom quote
const MAX_SITES = 20;
const MAX_SENSORS = 1000;

const ADDRESS_MAX_LENGTH = 200;
const DAY_MS = 24 * 60 * 60 * 1000;

// 08001 to 08042: Barcelona city
const BARCELONA_POSTAL_CODE = /^080(0[1-9]|[1-3]\d|4[0-2])$/;
const BARCELONA = "Barcelona";

const CARD_CLASS = "rounded-2xl border border-slate-200 bg-white p-6";
const TITLE_CLASS = "mb-4 font-bold text-slate-900";
const LABEL_CLASS = "mb-1 block text-xs font-semibold text-slate-700";

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

// A Barcelona postal code fills the city; it never overwrites what the client wrote
let cityFilled = false;

watch(
  () => form.postal_code.trim(),
  (code) => {
    if (BARCELONA_POSTAL_CODE.test(code)) {
      if (!form.city.trim()) {
        form.city = BARCELONA;
        cityFilled = true;
      }
    } else if (cityFilled && form.city === BARCELONA) {
      form.city = "";
      cityFilled = false;
    }
  },
);

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
} = useFieldErrors(FIELD_ORDER, { size: "lg" });
clearOnEdit({
  sites: () => form.sites,
  sensors: () => [form.sites, form.sensors],
  legal_name: () => form.legal_name,
  tax_id: () => form.tax_id,
  phone: () => form.phone,
  address: () => form.address,
  postal_code: () => form.postal_code,
  city: () => form.city,
  billing_email: () => form.billing_email,
  iban: () => form.iban,
  accept_terms: () => form.accept_terms,
  accept_sepa: () => form.accept_sepa,
});

const MESSAGE_BY_FIELD = {
  sites: `Elige entre 1 y ${MAX_SITES} edificios. Para más, escríbenos.`,
  sensors: `Elige entre 1 y ${MAX_SENSORS} sensores.`,
  legal_name: "Escribe la razón social (máximo 200 caracteres).",
  tax_id: "Escribe un CIF o NIF válido: entre 8 y 15 letras o números.",
  phone: "Escribe un teléfono español de 9 cifras, por ejemplo 612 345 678.",
  address: "Escribe la dirección fiscal.",
  postal_code: "Escribe un código postal de 5 cifras.",
  city: "Escribe la ciudad y la provincia (máximo 120 caracteres).",
  billing_email: "Escribe un email válido, por ejemplo facturas@empresa.com.",
  iban: "Revisa el IBAN: tiene que ser español, empieza por ES y tiene 24 caracteres.",
  accept_terms:
    "Tienes que aceptar las condiciones y la política de privacidad.",
  accept_sepa: "Tienes que autorizar la domiciliación para pagar por SEPA.",
};

// API errors of one field. The backend message is kept for the rules of
// shared/fields.py (phone, tax id, postal code); some codes get our text
const API_ERRORS = {
  codes: {
    SENSORS_BELOW_SITES: {
      field: "sensors",
      message: "Necesitas al menos un sensor por edificio.",
    },
    INVALID_TAX_ID: { field: "tax_id", message: MESSAGE_BY_FIELD.tax_id },
    INVALID_POSTAL_CODE: "postal_code",
    INVALID_PHONE: "phone",
    INVALID_IBAN: {
      field: "iban",
      message: "El IBAN no es válido: revisa los dígitos de la cuenta.",
    },
    TERMS_NOT_ACCEPTED: {
      field: "accept_terms",
      message: MESSAGE_BY_FIELD.accept_terms,
    },
    SEPA_NOT_ACCEPTED: {
      field: "accept_sepa",
      message: MESSAGE_BY_FIELD.accept_sepa,
    },
  },
  aliases: { billing_address: "address" },
  messages: MESSAGE_BY_FIELD,
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
    },
    {
      id: "YEARLY",
      label: "Anual",
      note: free === 1 ? "Un mes gratis" : `${free} meses gratis`,
      price: chosenPlan.value
        ? `${euros(billedPrice(chosenPlan.value, form.sensors, "YEARLY"))} / año`
        : "—",
    },
  ];
});

const chosenPeriod = computed(() =>
  periodOptions.value.find((option) => option.id === form.period),
);

// Spanish VAT, only shown: prices and the API stay without it
const VAT_PERCENT = 21;

const totalWithVat = computed(() => {
  if (!chosenPlan.value) return "";
  const billed = billedPrice(chosenPlan.value, form.sensors, form.period);
  const amount = new Intl.NumberFormat("es-ES", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format((billed * (100 + VAT_PERCENT)) / 100);
  return `${amount} € / ${form.period === "YEARLY" ? "año" : "mes"}`;
});

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
    value: chosenPlan.value ? `${euros(monthlyTotal.value)} + IVA` : "—",
  },
  // The API activates the account when it gets the request, not when the trial ends
  { label: "Empieza", value: "hoy, al confirmar el alta" },
]);

function hintId(field) {
  return `subscribe-${field}-hint`;
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
  return check({
    sites: sitesError,
    sensors: sensorsError,
    legal_name: () =>
      textProblem(form.legal_name, {
        max: 200,
        message: MESSAGE_BY_FIELD.legal_name,
      }),
    tax_id: () => taxIdProblem(form.tax_id),
    phone: () => phoneProblem(form.phone),
    address: () =>
      textProblem(form.address, {
        max: ADDRESS_MAX_LENGTH,
        message: MESSAGE_BY_FIELD.address,
      }),
    postal_code: () => postalCodeProblem(form.postal_code),
    city: () =>
      textProblem(form.city, { max: 120, message: MESSAGE_BY_FIELD.city }),
    billing_email: () => emailProblem(form.billing_email),
    iban: () => ibanProblem(form.iban),
    accept_terms: () => (form.accept_terms ? null : MESSAGE_BY_FIELD.accept_terms),
    accept_sepa: () => (form.accept_sepa ? null : MESSAGE_BY_FIELD.accept_sepa),
  });
}

function toPayload() {
  return {
    sites: form.sites,
    sensors: form.sensors,
    billing_period: form.period,
    legal_name: cleanText(form.legal_name),
    tax_id: form.tax_id.trim(),
    billing_address: cleanText(form.address),
    postal_code: form.postal_code.trim(),
    city: cleanText(form.city),
    billing_email: form.billing_email.trim(),
    phone: form.phone.trim(),
    iban: form.iban.trim(),
    accept_terms: form.accept_terms,
    accept_sepa: form.accept_sepa,
  };
}

// Turns an API error (already normalized by the adapter) into field or general messages
async function showApiError(err) {
  // Already a client (another tab, or an admin activated it): reload the session
  if (err?.code === "ORGANIZATION_NOT_IN_TRIAL") {
    await authStore.fetchMe();
    return;
  }

  // An error of a field: the code says which, or details[0].field
  // (CONTRACT_BELOW_CURRENT, the API message says how many it already has)
  if (applyApiError(err, API_ERRORS)) {
    // A building or sensor was added meanwhile: reload them for the minimums
    if (err.code === "CONTRACT_BELOW_CURRENT") {
      await sitesStore.fetchSites().catch(() => {});
    }
    return;
  }

  generalError.value = apiErrorMessage(
    err,
    "No hemos podido completar el alta. Inténtalo de nuevo en unos minutos.",
  );
}

async function onSubmit() {
  if (submitting.value) return;
  clear();
  generalError.value = "";
  if (!validate()) {
    await focusFirstError();
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
    await focusFirstError();
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
