<!--
  SENSOR FORM
  Fields of a sensor (#169), as in the A-Sensores mockup: name, device label
  (only on create), floor and pressure thresholds. Same pattern as SiteForm:
  v-model holds the sensor object and validate() checks it with the same
  rules as the API (B3), so the admin sees the error before sending.
  Rules:
    - floor between -basements and floors - 1 of its building (0 = ground floor)
    - thresholds between 0 and 25 bar, minimum lower than maximum
    - device label not used yet in the building, ignoring case (takenLabels)
  Usage:
    <SensorForm ref="sensorForm" v-model="sensor" :floors="site.floors" :basements="site.basements" mode="create" />
    if (sensorForm.value.validate()) { ... }
-->

<template>
  <div class="grid gap-4 sm:grid-cols-2">
    <div class="flex flex-col gap-1 sm:col-span-2">
      <label :for="fieldId('name')" class="text-sm font-semibold text-gray-700">
        Nombre <span aria-hidden="true">*</span>
      </label>
      <input
        :id="fieldId('name')"
        :ref="(el) => (inputs.name = el)"
        type="text"
        required
        :maxlength="NAME_MAX"
        autocomplete="off"
        placeholder="Cocina"
        :value="sensor.name"
        :class="inputClass('name')"
        :aria-invalid="Boolean(errors.name)"
        :aria-describedby="errors.name ? fieldId('name-error') : undefined"
        @input="update('name', $event.target.value)"
      />
      <p v-if="errors.name" :id="fieldId('name-error')" class="text-sm text-red-700">{{ errors.name }}</p>
    </div>

    <!-- The device label is set once: SensorUpdate cannot change it -->
    <div v-if="mode === 'create'" class="flex flex-col gap-1 sm:col-span-2">
      <label :for="fieldId('external_id')" class="text-sm font-semibold text-gray-700">
        Etiqueta del aparato <span aria-hidden="true">*</span>
      </label>
      <input
        :id="fieldId('external_id')"
        :ref="(el) => (inputs.external_id = el)"
        type="text"
        required
        :maxlength="EXTERNAL_ID_MAX"
        autocomplete="off"
        placeholder="SENS-001"
        :value="sensor.external_id"
        :class="inputClass('external_id')"
        :aria-invalid="Boolean(errors.external_id)"
        :aria-describedby="`${fieldId('external_id-hint')}${errors.external_id ? ' ' + fieldId('external_id-error') : ''}`"
        @input="update('external_id', $event.target.value)"
      />
      <p :id="fieldId('external_id-hint')" class="text-xs text-gray-500">
        La que lleva el sensor físico. No se puede repetir en el mismo edificio.
      </p>
      <p v-if="errors.external_id" :id="fieldId('external_id-error')" class="text-sm text-red-700">
        {{ errors.external_id }}
      </p>
    </div>

    <div class="flex flex-col gap-1 sm:col-span-2">
      <label :for="fieldId('floor')" class="text-sm font-semibold text-gray-700">
        Planta <span aria-hidden="true">*</span>
      </label>
      <select
        :id="fieldId('floor')"
        :ref="(el) => (inputs.floor = el)"
        :value="sensor.floor"
        :class="inputClass('floor')"
        :aria-invalid="Boolean(errors.floor)"
        :aria-describedby="`${fieldId('floor-hint')}${errors.floor ? ' ' + fieldId('floor-error') : ''}`"
        @change="update('floor', Number($event.target.value))"
      >
        <option v-for="floor in floorOptions" :key="floor" :value="floor">{{ floorLabel(floor) }}</option>
      </select>
      <p :id="fieldId('floor-hint')" class="text-xs text-gray-500">
        Solo las plantas del edificio: de {{ formatFloor(lowestFloor) }} a {{ formatFloor(highestFloor) }}.
      </p>
      <p v-if="errors.floor" :id="fieldId('floor-error')" class="text-sm text-red-700">{{ errors.floor }}</p>
    </div>

    <div class="flex flex-col gap-1">
      <label :for="fieldId('min_pressure')" class="text-sm font-semibold text-gray-700">
        Umbral mínimo (bar) <span aria-hidden="true">*</span>
      </label>
      <input
        :id="fieldId('min_pressure')"
        :ref="(el) => (inputs.min_pressure = el)"
        type="number"
        inputmode="decimal"
        required
        step="0.1"
        :min="PRESSURE_MIN"
        :max="PRESSURE_MAX"
        :value="sensor.min_pressure"
        :class="inputClass('min_pressure')"
        :aria-invalid="Boolean(errors.min_pressure)"
        :aria-describedby="`${fieldId('range-hint')}${errors.min_pressure ? ' ' + fieldId('min-error') : ''}`"
        @input="update('min_pressure', toNumber($event.target.value))"
      />
      <p v-if="errors.min_pressure" :id="fieldId('min-error')" class="text-sm text-red-700">
        {{ errors.min_pressure }}
      </p>
    </div>

    <div class="flex flex-col gap-1">
      <label :for="fieldId('max_pressure')" class="text-sm font-semibold text-gray-700">
        Umbral máximo (bar) <span aria-hidden="true">*</span>
      </label>
      <input
        :id="fieldId('max_pressure')"
        :ref="(el) => (inputs.max_pressure = el)"
        type="number"
        inputmode="decimal"
        required
        step="0.1"
        :min="PRESSURE_MIN"
        :max="PRESSURE_MAX"
        :value="sensor.max_pressure"
        :class="inputClass('max_pressure')"
        :aria-invalid="Boolean(errors.max_pressure)"
        :aria-describedby="`${fieldId('range-hint')}${errors.max_pressure ? ' ' + fieldId('max-error') : ''}`"
        @input="update('max_pressure', toNumber($event.target.value))"
      />
      <p v-if="errors.max_pressure" :id="fieldId('max-error')" class="text-sm text-red-700">
        {{ errors.max_pressure }}
      </p>
    </div>

    <p :id="fieldId('range-hint')" class="text-xs text-gray-500 sm:col-span-2">
      Rango permitido entre {{ PRESSURE_MIN }} y {{ PRESSURE_MAX }} bar.
    </p>
  </div>
</template>

<script>
// Empty sensor for the create form: ground floor, no thresholds yet
export function emptySensor() {
  return { name: '', external_id: '', floor: 0, min_pressure: '', max_pressure: '' }
}
</script>

<script setup>
import { computed, nextTick, reactive, useId } from 'vue'
import { floorLabel, floorRange } from '../utils/floors'

// Same limits as SensorBase / SensorCreate in the API (B3)
const NAME_MAX = 120
const EXTERNAL_ID_MAX = 100
const PRESSURE_MIN = 0
const PRESSURE_MAX = 25

// The sensor object: { name, external_id, floor, min_pressure, max_pressure }
const sensor = defineModel({ type: Object, required: true })

const props = defineProps({
  // Floors and basements of the building where the sensor is (B2)
  floors: { type: Number, required: true },
  basements: { type: Number, default: 0 },
  // 'create' asks for the device label; 'edit' cannot change it
  mode: { type: String, default: 'create', validator: (v) => ['create', 'edit'].includes(v) },
  // Device labels already used in this building. 'SENS-001' and 'sens-001'
  // are the same device, so the check ignores case and spaces
  takenLabels: { type: Array, default: () => [] },
})

// Same text whatever the case or the spaces around it
function sameLabel(a, b) {
  return String(a).trim().toLocaleLowerCase('es') === String(b).trim().toLocaleLowerCase('es')
}

// Unique prefix, so two forms on the same page never share ids
const uid = useId()
function fieldId(name) {
  return `sensor-${uid}-${name}`
}

// Floors of the building from top to bottom, same order as BuildingStack
const floorOptions = computed(() => floorRange(props.floors, props.basements))
const highestFloor = computed(() => floorOptions.value[0])
const lowestFloor = computed(() => floorOptions.value[floorOptions.value.length - 1])

// Real minus sign for basements: "de −2 a 3"
function formatFloor(floor) {
  return floor < 0 ? `−${-floor}` : String(floor)
}

// Inputs by field, to move the focus to the first field with an error
const inputs = {}

// Error message by field; empty when the field is valid
const errors = reactive({})

// Replaces the whole object instead of mutating the parent's one (one-way data flow)
function update(field, value) {
  sensor.value = { ...sensor.value, [field]: value }
  // An error disappears as soon as the user fixes the field. The two thresholds
  // depend on each other, so changing one also rechecks the other.
  const related = field === 'min_pressure' || field === 'max_pressure' ? ['min_pressure', 'max_pressure'] : [field]
  for (const name of related) {
    if (errors[name]) errors[name] = validators[name](sensor.value[name] ?? '')
  }
}

// Empty input stays '' so validation can say "required" instead of reading 0
function toNumber(text) {
  return text === '' ? '' : Number(text)
}

function isNumberBetween(value, min, max) {
  return typeof value === 'number' && Number.isFinite(value) && value >= min && value <= max
}

const rangeMessage = `Escribe un valor entre ${PRESSURE_MIN} y ${PRESSURE_MAX} bar.`

// Fields this form checks. external_id only exists on create
const fields = computed(() =>
  props.mode === 'create'
    ? ['name', 'external_id', 'floor', 'min_pressure', 'max_pressure']
    : ['name', 'floor', 'min_pressure', 'max_pressure']
)

// One rule per field. Each returns the error message, or '' when the value is valid
const validators = {
  name(value) {
    if (String(value).trim() === '') return 'Escribe el nombre del sensor.'
    if (value.length > NAME_MAX) return `Máximo ${NAME_MAX} caracteres.`
    return ''
  },
  external_id(value) {
    if (String(value).trim() === '') return 'Escribe la etiqueta del aparato.'
    if (value.length > EXTERNAL_ID_MAX) return `Máximo ${EXTERNAL_ID_MAX} caracteres.`
    const taken = props.takenLabels.find((label) => sameLabel(label, value))
    if (taken) return `Ya hay un sensor con la etiqueta ${taken} en este edificio.`
    return ''
  },
  floor(value) {
    return floorOptions.value.includes(value) ? '' : 'Elige una planta de este edificio.'
  },
  min_pressure(value) {
    return isNumberBetween(value, PRESSURE_MIN, PRESSURE_MAX) ? '' : rangeMessage
  },
  // Cross-field rule (same as the model_validator of B3): the message goes
  // on the maximum, as in the mockup
  max_pressure(value) {
    if (!isNumberBetween(value, PRESSURE_MIN, PRESSURE_MAX)) return rangeMessage
    const min = sensor.value.min_pressure
    if (isNumberBetween(min, PRESSURE_MIN, PRESSURE_MAX) && value <= min) {
      return 'El máximo debe ser mayor que el mínimo.'
    }
    return ''
  },
}

// Checks every field, shows the messages and focuses the first wrong field.
// Returns true when the sensor can be sent to the API.
function validate() {
  for (const field of fields.value) {
    errors[field] = validators[field](sensor.value[field] ?? '')
  }
  const firstWrong = fields.value.find((field) => errors[field])
  if (firstWrong) {
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
