<!--
  SITE FORM
  Fields of a building (site): name, address, floors, basements and type.
  Used by NewClientWizard (#168) and the sites view (#169).
  takenNames (optional): names of the client's other buildings, to reject a repeated one.
  v-model holds the site object; validate() checks it with the same limits as the API (B2).
  Usage:
    <SiteForm ref="siteForm" v-model="site" />
    if (siteForm.value.validate()) { ... }
    catch (err) { if (!siteForm.value.showApiError(err)) generalError = ... }
-->

<template>
  <div class="grid gap-4 sm:grid-cols-2">
    <div class="flex flex-col gap-1 sm:col-span-2">
      <label :for="fieldId('name')" class="text-sm font-semibold text-slate-700">
        Nombre del edificio <span aria-hidden="true">*</span>
      </label>
      <input
        :id="fieldId('name')"
        :ref="setRef('name')"
        type="text"
        :maxlength="NAME_MAX"
        autocomplete="off"
        :value="site.name"
        :class="inputClass('name')"
        v-bind="fieldAttrs('name')"
        @input="update('name', $event.target.value)"
      />
      <FieldError :id="errorId('name')" :message="errors.name" />
    </div>

    <div class="flex flex-col gap-1 sm:col-span-2">
      <label
        :for="fieldId('address')"
        class="text-sm font-semibold text-slate-700"
        >Dirección <span aria-hidden="true">*</span></label
      >
      <input
        :id="fieldId('address')"
        :ref="setRef('address')"
        type="text"
        required
        :maxlength="ADDRESS_MAX"
        autocomplete="street-address"
        placeholder="Carrer de Mallorca, 401"
        :value="site.address"
        :class="inputClass('address')"
        v-bind="fieldAttrs('address')"
        @input="update('address', $event.target.value)"
      />
      <FieldError :id="errorId('address')" :message="errors.address" />
    </div>

    <div class="flex flex-col gap-1">
      <label
        :for="fieldId('floors')"
        class="text-sm font-semibold text-slate-700"
      >
        Plantas sobre rasante <span aria-hidden="true">*</span>
      </label>
      <input
        :id="fieldId('floors')"
        :ref="setRef('floors')"
        type="number"
        inputmode="numeric"
        required
        min="1"
        :max="FLOORS_MAX"
        :value="site.floors"
        :class="inputClass('floors')"
        v-bind="fieldAttrs('floors', fieldId('floors-hint'))"
        @input="update('floors', toNumber($event.target.value))"
      />
      <p :id="fieldId('floors-hint')" class="text-xs text-slate-500">
        Cuenta la planta baja: un bajo sin pisos es 1.
      </p>
      <FieldError :id="errorId('floors')" :message="errors.floors" />
    </div>

    <div class="flex flex-col gap-1">
      <label
        :for="fieldId('basements')"
        class="text-sm font-semibold text-slate-700"
      >
        Sótanos <span aria-hidden="true">*</span>
      </label>
      <input
        :id="fieldId('basements')"
        :ref="setRef('basements')"
        type="number"
        inputmode="numeric"
        required
        min="0"
        :max="BASEMENTS_MAX"
        :value="site.basements"
        :class="inputClass('basements')"
        v-bind="fieldAttrs('basements')"
        @input="update('basements', toNumber($event.target.value))"
      />
      <FieldError :id="errorId('basements')" :message="errors.basements" />
    </div>

    <div class="flex flex-col gap-1 sm:col-span-2">
      <label :for="fieldId('type')" class="text-sm font-semibold text-slate-700"
        >Tipo de edificio</label
      >
      <select
        :id="fieldId('type')"
        :value="site.building_type"
        :class="inputClass('building_type')"
        @change="update('building_type', $event.target.value)"
      >
        <option
          v-for="type in BUILDING_TYPES"
          :key="type.value"
          :value="type.value"
        >
          {{ type.label }}
        </option>
      </select>
    </div>
  </div>
</template>

<script>
// Building types of the API (BuildingType enum, B2) with their Spanish labels.
// Exported so other views can show the label of a site's type.
export const BUILDING_TYPES = [
  { value: "RESIDENCE", label: "Residencia" },
  { value: "HOTEL", label: "Hotel" },
  { value: "COMMUNITY", label: "Comunidad de vecinos" },
  { value: "OFFICE", label: "Oficinas" },
  { value: "SPORTS", label: "Instalación deportiva" },
  { value: "INDUSTRIAL", label: "Industrial" },
  { value: "OTHER", label: "Otro" },
];

// Empty site with the API defaults (floors 1, basements 0, type OTHER)
export function emptySite() {
  return {
    name: "",
    address: "",
    floors: 1,
    basements: 0,
    building_type: "OTHER",
  };
}
</script>

<script setup>
import { useId } from "vue";
import FieldError from "./FieldError.vue";
import { useFieldErrors } from "../composables/useFieldErrors.js";
import {
  cleanText,
  integerProblem,
  textProblem,
  toNumber,
} from "../utils/validation.js";

// Same limits as SiteBase in the API (B2)
const NAME_MAX = 120;
const ADDRESS_MAX = 255;
const FLOORS_MAX = 200;
const BASEMENTS_MAX = 20;

// The site object: { name, address, floors, basements, building_type }
const site = defineModel({ type: Object, required: true });

const props = defineProps({
  // Names of the client's other buildings. The check ignores case and spaces,
  // so 'Torre Sofia' and 'torre sofia' count as the same building
  takenNames: { type: Array, default: () => [] },
});

// Same text whatever the case or the spaces around it
function sameName(a, b) {
  return (
    cleanText(a).toLocaleLowerCase("es") === cleanText(b).toLocaleLowerCase("es")
  );
}

// Unique prefix, so two forms on the same page never share ids
const uid = useId();
function fieldId(name) {
  return `site-${uid}-${name}`;
}

// Fields in screen order: the first one with an error gets the focus
const {
  errors,
  errorId,
  setRef,
  inputClass,
  fieldAttrs,
  check,
  focusFirstError,
  clearOnEdit,
  applyApiError,
} = useFieldErrors(["name", "address", "floors", "basements", "building_type"]);
clearOnEdit({
  name: () => site.value.name,
  address: () => site.value.address,
  floors: () => site.value.floors,
  basements: () => site.value.basements,
});

// Replaces the whole object instead of mutating the parent's one (one-way data flow)
function update(field, value) {
  site.value = { ...site.value, [field]: value };
}

// One rule per field: the message, or null when the value is valid
const rules = {
  name: () => {
    const problem = textProblem(site.value.name, {
      max: NAME_MAX,
      message: `Escribe el nombre del edificio (máximo ${NAME_MAX} caracteres).`,
    });
    if (problem) return problem;
    return props.takenNames.some((name) => sameName(name, site.value.name))
      ? "Este cliente ya tiene un edificio con ese nombre."
      : null;
  },
  address: () =>
    textProblem(site.value.address, {
      max: ADDRESS_MAX,
      message: `Escribe la dirección (máximo ${ADDRESS_MAX} caracteres).`,
    }),
  floors: () => integerProblem(site.value.floors, 1, FLOORS_MAX),
  basements: () => integerProblem(site.value.basements, 0, BASEMENTS_MAX),
};

// Checks every field, shows the messages and focuses the first wrong field.
// Returns true when the site can be sent to the API.
function validate() {
  if (check(rules)) return true;
  focusFirstError();
  return false;
}

// API errors of one field; the backend message says what is wrong
const API_ERRORS = {
  codes: {
    SITE_NAME_TAKEN: "name",
    INVALID_NAME: "name",
    INVALID_FLOORS: "floors",
    INVALID_BUILDING_TYPE: "building_type",
  },
  aliases: { "first_site.name": "name", "first_site.address": "address" },
  messages: {
    name: `Escribe el nombre del edificio (máximo ${NAME_MAX} caracteres).`,
    address: `Escribe la dirección (máximo ${ADDRESS_MAX} caracteres).`,
    floors: `Escribe un número entero entre 1 y ${FLOORS_MAX}.`,
    basements: `Escribe un número entero entre 0 y ${BASEMENTS_MAX}.`,
  },
};

// Puts an API error under its field. Returns false when it is not of a
// field, so the parent shows it as a general error (<FormError>)
function showApiError(error) {
  if (!applyApiError(error, API_ERRORS)) return false;
  focusFirstError();
  return true;
}

// The parent calls validate() and showApiError() through a template ref
defineExpose({ validate, showApiError });
</script>
