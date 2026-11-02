<!--
  NEW CLIENT WIZARD
  Four-step form to sign up a client: 1 Cliente, 2 Edificio, 3 Usuario, 4 Facturación.
  It only collects and validates the data; the parent creates the client and passes
  the result back in `created`, then the wizard shows the invitation link to send.
  While the parent is saving, `submitting` disables the buttons; an API error comes
  back in `serverError` ({ field, message }): an error of a field returns to its step.
  With `checkName`, step 1 asks the API if the name is free before moving on.
  Usage:
    <NewClientWizard :created="result" :check-name="isNameTaken" :submitting="saving"
      :server-error="apiError" @submit="create" @cancel="close" @open="goToClient" />
-->

<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
    <!-- Success: the client exists, now the admin sends the invitation link -->
    <div v-if="created" class="space-y-4">
      <div class="flex items-center gap-3">
        <span
          class="flex h-9 w-9 items-center justify-center rounded-full bg-success-light text-success-dark"
          aria-hidden="true"
          >✓</span
        >
        <h2
          ref="heading"
          tabindex="-1"
          class="text-xl font-bold text-slate-900 focus:outline-none"
        >
          {{ created.client.name }} creado
        </h2>
      </div>
      <template v-if="created.invitation">
        <p class="text-slate-700">
          Envía este enlace a {{ created.invitation.name }} ({{
            created.invitation.email
          }}) para que active su cuenta.
        </p>
        <InviteLinkCopy
          :link="created.invitation.link"
          :expires-at="created.invitation.expires_at"
        />
      </template>
      <!-- The client exists but the invitation failed: it can be sent again from the client page -->
      <p
        v-else
        role="alert"
        class="rounded-lg border border-warning/40 bg-warning-light px-4 py-3 text-warning-dark"
      >
        No se ha podido crear la invitación. Puedes enviarla desde la pestaña
        Usuarios de la ficha del cliente.
      </p>
      <div class="flex flex-wrap gap-3 border-t border-slate-200 pt-4">
        <button
          type="button"
          :class="BUTTON_PRIMARY"
          @click="$emit('open', created.client)"
        >
          Ir a la ficha del cliente
        </button>
        <button
          type="button"
          :class="BUTTON_SECONDARY"
          @click="$emit('cancel')"
        >
          Volver a la lista
        </button>
      </div>
    </div>

    <form v-else novalidate class="space-y-6" @submit.prevent="next">
      <div class="space-y-4">
        <h2 class="text-xl font-bold text-slate-900">Nuevo cliente</h2>

        <!-- Progress: one bar per step; aria-current marks the current one -->
        <ol aria-label="Pasos del alta" class="grid grid-cols-4 gap-2">
          <li
            v-for="(label, index) in STEPS"
            :key="label"
            class="flex flex-col gap-1.5 text-xs font-semibold sm:text-sm"
            :class="index <= step ? 'text-aqua-600' : 'text-slate-500'"
            :aria-current="index === step ? 'step' : undefined"
          >
            <span
              class="block h-1.5 rounded-full"
              :class="index <= step ? 'bg-aqua-600' : 'bg-slate-200'"
            ></span>
            <span>
              {{ index + 1 }}. {{ label }}
              <span v-if="index < step" class="sr-only">(completado)</span>
            </span>
          </li>
        </ol>
      </div>

      <!-- Step title receives the focus when the step changes, so keyboard and
           screen reader users start reading the new step from the top -->
      <h3
        ref="heading"
        tabindex="-1"
        class="text-lg font-semibold text-slate-800 focus:outline-none"
      >
        Paso {{ step + 1 }} de {{ STEPS.length }}: {{ STEP_TITLES[step] }}
      </h3>

      <!-- 1. Cliente -->
      <div v-if="step === 0" class="grid gap-4 sm:grid-cols-2">
        <div class="flex flex-col gap-1 sm:col-span-2">
          <label
            :for="fieldId('name')"
            class="text-sm font-semibold text-slate-700"
          >
            Nombre del cliente <span aria-hidden="true">*</span>
          </label>
          <input
            :id="fieldId('name')"
            :ref="setRef('name')"
            v-model="form.client.name"
            type="text"
            required
            maxlength="120"
            autocomplete="organization"
            :class="inputClass('name')"
            v-bind="fieldAttrs('name')"
          />
          <FieldError :id="errorId('name')" :message="errors.name" />
        </div>
        <div class="flex flex-col gap-1">
          <label
            :for="fieldId('contact_email')"
            class="text-sm font-semibold text-slate-700"
            >Email de contacto <span aria-hidden="true">*</span></label
          >
          <input
            :id="fieldId('contact_email')"
            :ref="setRef('contact_email')"
            v-model="form.client.contact_email"
            type="email"
            required
            autocomplete="email"
            :class="inputClass('contact_email')"
            v-bind="fieldAttrs('contact_email')"
          />
          <FieldError :id="errorId('contact_email')" :message="errors.contact_email" />
        </div>
        <div class="flex flex-col gap-1">
          <label
            :for="fieldId('phone')"
            class="text-sm font-semibold text-slate-700"
            >Teléfono <span aria-hidden="true">*</span></label
          >
          <input
            :id="fieldId('phone')"
            :ref="setRef('phone')"
            v-model="form.client.phone"
            type="tel"
            required
            maxlength="30"
            autocomplete="tel"
            :class="inputClass('phone')"
            v-bind="fieldAttrs('phone')"
          />
          <FieldError :id="errorId('phone')" :message="errors.phone" />
        </div>
        <p class="text-sm text-slate-600 sm:col-span-2">
          AquaGuard solo da servicio en Barcelona.
        </p>
      </div>

      <!-- 2. Edificio: the same form the sites view uses -->
      <SiteForm v-else-if="step === 1" ref="siteForm" v-model="form.site" />

      <!-- 3. Usuario: receives the invitation link -->
      <div v-else-if="step === 2" class="grid gap-4 sm:grid-cols-2">
        <p class="text-sm text-slate-600 sm:col-span-2">
          Al crear el cliente obtendrás un enlace de invitación para enviar a
          esta persona.
        </p>
        <div class="flex flex-col gap-1">
          <label
            :for="fieldId('user_name')"
            class="text-sm font-semibold text-slate-700"
          >
            Nombre <span aria-hidden="true">*</span>
          </label>
          <input
            :id="fieldId('user_name')"
            :ref="setRef('user_name')"
            v-model="form.user.name"
            type="text"
            maxlength="120"
            required
            autocomplete="name"
            :class="inputClass('user_name')"
            v-bind="fieldAttrs('user_name')"
          />
          <FieldError :id="errorId('user_name')" :message="errors.user_name" />
        </div>
        <div class="flex flex-col gap-1">
          <label
            :for="fieldId('user_email')"
            class="text-sm font-semibold text-slate-700"
          >
            Email <span aria-hidden="true">*</span>
          </label>
          <input
            :id="fieldId('user_email')"
            :ref="setRef('user_email')"
            v-model="form.user.email"
            type="email"
            required
            autocomplete="email"
            :class="inputClass('user_email')"
            v-bind="fieldAttrs('user_email')"
          />
          <FieldError :id="errorId('user_email')" :message="errors.user_email" />
        </div>
      </div>

      <!-- 4. Facturación: optional, it can be completed later -->
      <div v-else class="grid gap-4 sm:grid-cols-2">
        <p class="text-sm text-slate-600 sm:col-span-2">
          Opcional: se puede completar más tarde.
        </p>
        <div class="flex flex-col gap-1">
          <label
            :for="fieldId('legal_name')"
            class="text-sm font-semibold text-slate-700"
            >Razón social</label
          >
          <input
            :id="fieldId('legal_name')"
            :ref="setRef('legal_name')"
            v-model="form.client.legal_name"
            type="text"
            maxlength="200"
            :class="inputClass('legal_name')"
            v-bind="fieldAttrs('legal_name')"
          />
          <FieldError :id="errorId('legal_name')" :message="errors.legal_name" />
        </div>
        <div class="flex flex-col gap-1">
          <label
            :for="fieldId('tax_id')"
            class="text-sm font-semibold text-slate-700"
            >NIF o CIF</label
          >
          <input
            :id="fieldId('tax_id')"
            :ref="setRef('tax_id')"
            v-model="form.client.tax_id"
            type="text"
            maxlength="30"
            :class="inputClass('tax_id')"
            v-bind="fieldAttrs('tax_id')"
          />
          <FieldError :id="errorId('tax_id')" :message="errors.tax_id" />
        </div>
        <div class="flex flex-col gap-1 sm:col-span-2">
          <label
            :for="fieldId('billing_email')"
            class="text-sm font-semibold text-slate-700"
            >Email de facturación</label
          >
          <input
            :id="fieldId('billing_email')"
            :ref="setRef('billing_email')"
            v-model="form.client.billing_email"
            type="email"
            autocomplete="email"
            :class="inputClass('billing_email')"
            v-bind="fieldAttrs('billing_email')"
          />
          <FieldError :id="errorId('billing_email')" :message="errors.billing_email" />
        </div>
      </div>

      <!-- API error that does not belong to a field of this wizard -->
      <FormError ref="generalErrorMessage" :message="generalError" />

      <div class="flex justify-between gap-3 border-t border-slate-200 pt-4">
        <button
          type="button"
          :class="BUTTON_SECONDARY"
          :disabled="busy"
          @click="back"
        >
          {{ step === 0 ? "Cancelar" : "Atrás" }}
        </button>
        <!-- type="submit": Enter in any field also moves forward -->
        <button
          type="submit"
          :class="BUTTON_PRIMARY"
          :disabled="busy"
          :aria-busy="busy"
        >
          {{ submitLabel }}
        </button>
      </div>
    </form>
  </section>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick, useId } from "vue";
import SiteForm, { emptySite } from "./SiteForm.vue";
import InviteLinkCopy from "./InviteLinkCopy.vue";
import FieldError from "./FieldError.vue";
import FormError from "./FormError.vue";
import { useFieldErrors } from "../composables/useFieldErrors.js";
// Same rules and messages as every other form and the API (utils/validation.js)
import {
  cleanText,
  emailProblem,
  organizationNameProblem,
  personNameProblem,
  phoneProblem,
  taxIdProblem,
  textProblem,
} from "../utils/validation.js";

const props = defineProps({
  // Set by the parent after creating: { client, invitation: { name, email, link, expires_at } | null }
  created: { type: Object, default: null },
  // True while the parent is calling the API
  submitting: { type: Boolean, default: false },
  // API error after "Crear cliente": { field, message }. An error of a field goes back to its step
  serverError: { type: Object, default: null },
  // Optional async (name) => true when the name is already used. Checked on "Siguiente" in step 1
  checkName: { type: Function, default: null },
});

const emit = defineEmits(["submit", "cancel", "open"]);

const STEPS = ["Cliente", "Edificio", "Usuario", "Facturación"];
const STEP_TITLES = [
  "datos del cliente",
  "primer edificio",
  "primer usuario",
  "facturación",
];

const BUTTON_PRIMARY =
  "min-h-10 rounded-lg bg-aqua-600 px-4 text-sm font-semibold text-white hover:bg-aqua-700 disabled:cursor-wait disabled:opacity-60";
const BUTTON_SECONDARY =
  "min-h-10 rounded-lg border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700 hover:border-aqua-600 disabled:opacity-60";

// Same limit as OrganizationContact.legal_name (B1)
const LEGAL_NAME_MAX = 200;

const step = ref(0);
const isLastStep = computed(() => step.value === STEPS.length - 1);

// True while step 1 waits for the name check
const checking = ref(false);
const busy = computed(() => props.submitting || checking.value);

const submitLabel = computed(() => {
  if (checking.value) return "Comprobando…";
  if (!isLastStep.value) return "Siguiente";
  return props.submitting ? "Creando cliente…" : "Crear cliente";
});

// API error shown above the buttons (not tied to a field)
const generalError = ref("");
const generalErrorMessage = ref(null);

// Everything the wizard collects, grouped as the parent will send it
const form = reactive({
  client: {
    name: "",
    contact_email: "",
    phone: "",
    legal_name: "",
    tax_id: "",
    billing_email: "",
  },
  site: emptySite(),
  user: { name: "", email: "" },
});

const heading = ref(null);
const siteForm = ref(null);

const uid = useId();
function fieldId(name) {
  return `wizard-${uid}-${name}`;
}

// Step of each field, in screen order: an API error takes the admin back there
const FIELD_STEP = {
  name: 0,
  contact_email: 0,
  phone: 0,
  user_name: 2,
  user_email: 2,
  legal_name: 3,
  tax_id: 3,
  billing_email: 3,
};

const {
  errors,
  inputs,
  errorId,
  setRef,
  inputClass,
  fieldAttrs,
  check,
  focusFirstError,
  clearOnEdit,
} = useFieldErrors(Object.keys(FIELD_STEP));
clearOnEdit({
  name: () => form.client.name,
  contact_email: () => form.client.contact_email,
  phone: () => form.client.phone,
  user_name: () => form.user.name,
  user_email: () => form.user.email,
  legal_name: () => form.client.legal_name,
  tax_id: () => form.client.tax_id,
  billing_email: () => form.client.billing_email,
});

// Rules of each step (the building step is validated by SiteForm itself).
// Each returns the error message of a field, or null when the value is valid
const STEP_RULES = [
  {
    name: () => organizationNameProblem(form.client.name),
    contact_email: () => emailProblem(form.client.contact_email),
    phone: () => phoneProblem(form.client.phone),
  },
  {},
  {
    user_name: () => personNameProblem(form.user.name),
    user_email: () => emailProblem(form.user.email),
  },
  {
    // Optional step: an empty field is fine, a wrong one is not
    legal_name: () =>
      form.client.legal_name.trim()
        ? textProblem(form.client.legal_name, {
            max: LEGAL_NAME_MAX,
            message: `Escribe la razón social (máximo ${LEGAL_NAME_MAX} caracteres).`,
          })
        : null,
    tax_id: () => taxIdProblem(form.client.tax_id, { required: false }),
    billing_email: () =>
      emailProblem(form.client.billing_email, { required: false }),
  },
];

// Validates the current step; focuses the first wrong field and returns false if any
function validateStep() {
  if (step.value === 1) {
    return siteForm.value.validate();
  }

  if (check(STEP_RULES[step.value])) return true;
  focusFirstError();
  return false;
}

// Step 1: asks the API whether the name is free. If the check itself fails
// (network, server), the admin can go on: "Crear cliente" checks it again (409)
async function nameIsFree() {
  if (!props.checkName) return true;
  checking.value = true;
  try {
    const taken = await props.checkName(form.client.name);
    if (!taken) return true;
    errors.name = "Ya hay un cliente con este nombre.";
    focusFirstError();
    return false;
  } catch {
    return true;
  } finally {
    checking.value = false;
  }
}

async function next() {
  if (busy.value) return;
  generalError.value = "";
  if (!validateStep()) return;
  if (step.value === 0 && !(await nameIsFree())) return;
  if (isLastStep.value) {
    emit("submit", {
      client: { ...form.client },
      site: { ...form.site },
      user: { name: cleanText(form.user.name), email: form.user.email.trim() },
    });
  } else {
    step.value += 1;
  }
}

function back() {
  if (step.value === 0) emit("cancel");
  else step.value -= 1;
}

// Field to focus instead of the title after the next step change (set by an API error)
let focusAfterStep = null;

// Move the focus to the title of the new step, or to the success message
watch([step, () => props.created], () =>
  nextTick(() => {
    const target = focusAfterStep ? inputs[focusAfterStep] : heading.value;
    focusAfterStep = null;
    target?.focus();
  }),
);

// API error after submitting. An error of a field (repeated name, phone
// that is not Spanish...) goes back to its step and marks the field; any
// other error is shown above the buttons
watch(
  () => props.serverError,
  (serverError) => {
    if (!serverError) return;
    const field = serverError.field;
    if (field in FIELD_STEP) {
      errors[field] = serverError.message;
      if (step.value === FIELD_STEP[field]) {
        focusFirstError();
      } else {
        focusAfterStep = field;
        step.value = FIELD_STEP[field];
      }
    } else {
      generalError.value = serverError.message;
      nextTick(() => generalErrorMessage.value?.focus());
    }
  },
);
</script>
