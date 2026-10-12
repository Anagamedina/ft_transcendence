<!--
  SITE FORM
  Fields of a building (site): name, address, floors, basements and type.
  Used by NewClientWizard (#168) and reusable in the sites view (#169).
  v-model holds the site object; validate() checks it with the same limits as the API (B2).
  Usage:
    <SiteForm ref="siteForm" v-model="site" />
    if (siteForm.value.validate()) { ... }
-->

<template>
  <div class="grid gap-4 sm:grid-cols-2">
    <div class="flex flex-col gap-1 sm:col-span-2">
      <label :for="fieldId('name')" class="text-sm font-semibold text-gray-700">
        Nombre del edificio <span aria-hidden="true">*</span>
      </label>
      <input
        :id="fieldId('name')"
        :ref="(el) => (inputs.name = el)"
        type="text"
        required
        maxlength="120"
        autocomplete="off"
        :value="site.name"
        :class="inputClass('name')"
        :aria-invalid="Boolean(errors.name)"
        :aria-describedby="errors.name ? fieldId('name-error') : undefined"
        @input="update('name', $event.target.value)"
      />
      <p v-if="errors.name" :id="fieldId('name-error')" class="text-sm text-red-700">{{ errors.name }}</p>
    </div>

    <div class="flex flex-col gap-1 sm:col-span-2">
      <label :for="fieldId('address')" class="text-sm font-semibold text-gray-700">Dirección</label>
      <input
        :id="fieldId('address')"
        :ref="(el) => (inputs.address = el)"
        type="text"
        maxlength="255"
        autocomplete="street-address"
        placeholder="Carrer de Mallorca, 401"
        :value="site.address"
        :class="inputClass('address')"
        :aria-invalid="Boolean(errors.address)"
        :aria-describedby="errors.address ? fieldId('address-error') : undefined"
        @input="update('address', $event.target.value)"
      />
      <p v-if="errors.address" :id="fieldId('address-error')" class="text-sm text-red-700">
        {{ errors.address }}
      </p>
    </div>

    <div class="flex flex-col gap-1">
      <label :for="fieldId('floors')" class="text-sm font-semibold text-gray-700">
        Plantas sobre rasante <span aria-hidden="true">*</span>
      </label>
      <input
        :id="fieldId('floors')"
        :ref="(el) => (inputs.floors = el)"
        type="number"
        inputmode="numeric"
        required
        min="1"
        :max="FLOORS_MAX"
        :value="site.floors"
        :class="inputClass('floors')"
        :aria-invalid="Boolean(errors.floors)"
        :aria-describedby="`${fieldId('floors-hint')}${errors.floors ? ' ' + fieldId('floors-error') : ''}`"
        @input="update('floors', toNumber($event.target.value))"
      />
      <p :id="fieldId('floors-hint')" class="text-xs text-gray-500">Cuenta la planta baja: un bajo sin pisos es 1.</p>
      <p v-if="errors.floors" :id="fieldId('floors-error')" class="text-sm text-red-700">{{ errors.floors }}</p>
    </div>

    <div class="flex flex-col gap-1">
      <label :for="fieldId('basements')" class="text-sm font-semibold text-gray-700">
        Sótanos <span aria-hidden="true">*</span>
      </label>
      <input
        :id="fieldId('basements')"
        :ref="(el) => (inputs.basements = el)"
        type="number"
        inputmode="numeric"
        required
        min="0"
        :max="BASEMENTS_MAX"
        :value="site.basements"
        :class="inputClass('basements')"
        :aria-invalid="Boolean(errors.basements)"
        :aria-describedby="errors.basements ? fieldId('basements-error') : undefined"
        @input="update('basements', toNumber($event.target.value))"
      />
      <p v-if="errors.basements" :id="fieldId('basements-error')" class="text-sm text-red-700">
        {{ errors.basements }}
      </p>
    </div>

    <div class="flex flex-col gap-1 sm:col-span-2">
      <label :for="fieldId('type')" class="text-sm font-semibold text-gray-700">Tipo de edificio</label>
      <select
        :id="fieldId('type')"
        :value="site.building_type"
        :class="inputClass('building_type')"
        @change="update('building_type', $event.target.value)"
      >
        <option v-for="type in BUILDING_TYPES" :key="type.value" :value="type.value">
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
  { value: 'RESIDENCE', label: 'Residencia' },
  { value: 'HOTEL', label: 'Hotel' },
  { value: 'COMMUNITY', label: 'Comunidad de vecinos' },
  { value: 'OFFICE', label: 'Oficinas' },
  { value: 'SPORTS', label: 'Instalación deportiva' },
  { value: 'INDUSTRIAL', label: 'Industrial' },
  { value: 'OTHER', label: 'Otro' },
]

// Empty site with the API defaults (floors 1, basements 0, type OTHER)
export function emptySite() {
  return { name: '', address: '', floors: 1, basements: 0, building_type: 'OTHER' }
}
</script>

<script setup>
import { reactive, nextTick, useId } from 'vue'

// Same limits as SiteBase in the API (B2)
const NAME_MAX = 120
const ADDRESS_MAX = 255
const FLOORS_MAX = 200
const BASEMENTS_MAX = 20

// The site object: { name, address, floors, basements, building_type }
const site = defineModel({ type: Object, required: true })

// Unique prefix, so two forms on the same page never share ids
const uid = useId()
function fieldId(name) {
  return `site-${uid}-${name}`
}

// Inputs by field, to move the focus to the first field with an error
const inputs = {}

// Error message by field; empty when the field is valid
const errors = reactive({})

// Replaces the whole object instead of mutating the parent's one (one-way data flow)
function update(field, value) {
  site.value = { ...site.value, [field]: value }
  // The error disappears as soon as the user fixes the field
  if (errors[field]) errors[field] = validators[field]?.(value) ?? ''
}

// Empty input stays '' so validation can say "required" instead of reading 0
function toNumber(text) {
  return text === '' ? '' : Number(text)
}

function isIntegerBetween(value, min, max) {
  return Number.isInteger(value) && value >= min && value <= max
}

// One rule per field. Each returns the error message, or '' when the value is valid
const validators = {
  name(value) {
    if (value.trim() === '') return 'Escribe el nombre del edificio.'
    if (value.length > NAME_MAX) return `Máximo ${NAME_MAX} caracteres.`
    return ''
  },
  address(value) {
    return value.length > ADDRESS_MAX ? `Máximo ${ADDRESS_MAX} caracteres.` : ''
  },
  floors(value) {
    return isIntegerBetween(value, 1, FLOORS_MAX) ? '' : `Escribe un número entero entre 1 y ${FLOORS_MAX}.`
  },
  basements(value) {
    return isIntegerBetween(value, 0, BASEMENTS_MAX) ? '' : `Escribe un número entero entre 0 y ${BASEMENTS_MAX}.`
  },
}

// Checks every field, shows the messages and focuses the first wrong field.
// Returns true when the site can be sent to the API.
function validate() {
  for (const field of Object.keys(validators)) {
    errors[field] = validators[field](site.value[field] ?? '')
  }
  const firstWrong = Object.keys(validators).find((field) => errors[field])
  if (firstWrong) {
    // Wait until the error messages are rendered, then move the focus there
    nextTick(() => inputs[firstWrong]?.focus())
    return false
  }
  return true
}

function inputClass(field) {
  const base =
    'w-full rounded-lg border bg-white px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-aqua-600'
  return errors[field] ? `${base} border-red-600` : `${base} border-gray-300`
}

// The parent calls validate() through a template ref
defineExpose({ validate })
</script>
