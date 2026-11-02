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
      <label :for="fieldId('name')" class="text-sm font-semibold text-slate-700">
        Nombre <span aria-hidden="true">*</span>
      </label>
      <input
        :id="fieldId('name')"
        :ref="setRef('name')"
        type="text"
        required
        :maxlength="NAME_MAX"
        autocomplete="off"
        placeholder="Cocina"
        :value="sensor.name"
        :class="inputClass('name')"
        v-bind="fieldAttrs('name')"
        @input="update('name', $event.target.value)"
      />
      <FieldError :id="errorId('name')" :message="errors.name" />
    </div>

    <!-- The device label is set once: SensorUpdate cannot change it -->
    <div v-if="mode === 'create'" class="flex flex-col gap-1 sm:col-span-2">
      <label
        :for="fieldId('external_id')"
        class="text-sm font-semibold text-slate-700"
      >
        Etiqueta del aparato <span aria-hidden="true">*</span>
      </label>
      <input
        :id="fieldId('external_id')"
        :ref="setRef('external_id')"
        type="text"
        required
        :maxlength="EXTERNAL_ID_MAX"
        autocomplete="off"
        placeholder="SENS-001"
        :value="sensor.external_id"
        :class="inputClass('external_id')"
        v-bind="fieldAttrs('external_id', fieldId('external_id-hint'))"
        @input="update('external_id', $event.target.value)"
      />
      <p :id="fieldId('external_id-hint')" class="text-xs text-slate-500">
        La que lleva el sensor físico. No se puede repetir en el mismo edificio.
      </p>
      <FieldError :id="errorId('external_id')" :message="errors.external_id" />
    </div>

    <div class="flex flex-col gap-1 sm:col-span-2">
      <label
        :for="fieldId('floor')"
        class="text-sm font-semibold text-slate-700"
      >
        Planta <span aria-hidden="true">*</span>
      </label>
      <select
        :id="fieldId('floor')"
        :ref="setRef('floor')"
        :value="sensor.floor"
        :class="inputClass('floor')"
        v-bind="fieldAttrs('floor', fieldId('floor-hint'))"
        @change="update('floor', Number($event.target.value))"
      >
        <option v-for="floor in floorOptions" :key="floor" :value="floor">
          {{ floorLabel(floor) }}
        </option>
      </select>
      <p :id="fieldId('floor-hint')" class="text-xs text-slate-500">
        Solo las plantas del edificio: de {{ formatFloor(lowestFloor) }} a
        {{ formatFloor(highestFloor) }}.
      </p>
      <FieldError :id="errorId('floor')" :message="errors.floor" />
    </div>

    <div class="flex flex-col gap-1">
      <label
        :for="fieldId('min_pressure')"
        class="text-sm font-semibold text-slate-700"
      >
        Umbral mínimo (bar) <span aria-hidden="true">*</span>
      </label>
      <input
        :id="fieldId('min_pressure')"
        :ref="setRef('min_pressure')"
        type="number"
        inputmode="decimal"
        required
        step="0.1"
        :min="PRESSURE_MIN"
        :max="PRESSURE_MAX"
        :value="sensor.min_pressure"
        :class="inputClass('min_pressure')"
        v-bind="fieldAttrs('min_pressure', fieldId('range-hint'))"
        @input="update('min_pressure', toNumber($event.target.value))"
      />
      <FieldError :id="errorId('min_pressure')" :message="errors.min_pressure" />
    </div>

    <div class="flex flex-col gap-1">
      <label
        :for="fieldId('max_pressure')"
        class="text-sm font-semibold text-slate-700"
      >
        Umbral máximo (bar) <span aria-hidden="true">*</span>
      </label>
      <input
        :id="fieldId('max_pressure')"
        :ref="setRef('max_pressure')"
        type="number"
        inputmode="decimal"
        required
        step="0.1"
        :min="PRESSURE_MIN"
        :max="PRESSURE_MAX"
        :value="sensor.max_pressure"
        :class="inputClass('max_pressure')"
        v-bind="fieldAttrs('max_pressure', fieldId('range-hint'))"
        @input="update('max_pressure', toNumber($event.target.value))"
      />
      <FieldError :id="errorId('max_pressure')" :message="errors.max_pressure" />
    </div>

    <p :id="fieldId('range-hint')" class="text-xs text-slate-500 sm:col-span-2">
      Rango permitido entre {{ PRESSURE_MIN }} y {{ PRESSURE_MAX }} bar.
    </p>
  </div>
</template>

<script>
// Empty sensor for the create form: ground floor, no thresholds yet
export function emptySensor() {
  return {
    name: "",
    external_id: "",
    floor: 0,
    min_pressure: "",
    max_pressure: "",
  };
}
</script>

<script setup>
import { computed, useId } from "vue";
import FieldError from "./FieldError.vue";
import { useFieldErrors } from "../composables/useFieldErrors.js";
import { floorLabel, floorRange } from "../utils/floors";
import {
  cleanText,
  numberProblem,
  textProblem,
  toNumber,
} from "../utils/validation.js";

// Same limits as SensorBase / SensorCreate in the API (B3)
const NAME_MAX = 120;
const EXTERNAL_ID_MAX = 100;
const PRESSURE_MIN = 0;
const PRESSURE_MAX = 25;

// The sensor object: { name, external_id, floor, min_pressure, max_pressure }
const sensor = defineModel({ type: Object, required: true });

const props = defineProps({
  // Floors and basements of the building where the sensor is (B2)
  floors: { type: Number, required: true },
  basements: { type: Number, default: 0 },
  // 'create' asks for the device label; 'edit' cannot change it
  mode: {
    type: String,
    default: "create",
    validator: (v) => ["create", "edit"].includes(v),
  },
  // Device labels already used in this building. 'SENS-001' and 'sens-001'
  // are the same device, so the check ignores case and spaces
  takenLabels: { type: Array, default: () => [] },
});

// Same text whatever the case or the spaces around it
function sameLabel(a, b) {
  return (
    cleanText(a).toLocaleLowerCase("es") === cleanText(b).toLocaleLowerCase("es")
  );
}

// Unique prefix, so two forms on the same page never share ids
const uid = useId();
function fieldId(name) {
  return `sensor-${uid}-${name}`;
}

// Floors of the building from top to bottom, same order as BuildingStack
const floorOptions = computed(() => floorRange(props.floors, props.basements));
const highestFloor = computed(() => floorOptions.value[0]);
const lowestFloor = computed(
  () => floorOptions.value[floorOptions.value.length - 1],
);

// Real minus sign for basements: "de −2 a 3"
function formatFloor(floor) {
  return floor < 0 ? `−${-floor}` : String(floor);
}

// Fields in screen order: the first one with an error gets the focus.
// external_id only exists on create; check() only looks at the rules it gets
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
} = useFieldErrors([
  "name",
  "external_id",
  "floor",
  "min_pressure",
  "max_pressure",
]);
// The two thresholds depend on each other: editing one clears both errors
const thresholds = () => [sensor.value.min_pressure, sensor.value.max_pressure];
clearOnEdit({
  name: () => sensor.value.name,
  external_id: () => sensor.value.external_id,
  floor: () => sensor.value.floor,
  min_pressure: thresholds,
  max_pressure: thresholds,
});

// Replaces the whole object instead of mutating the parent's one (one-way data flow)
function update(field, value) {
  sensor.value = { ...sensor.value, [field]: value };
}

const rangeMessage = `Escribe un valor entre ${PRESSURE_MIN} y ${PRESSURE_MAX} bar.`;

function pressureProblem(value) {
  return numberProblem(value, PRESSURE_MIN, PRESSURE_MAX) && rangeMessage;
}

// One rule per field: the message, or null when the value is valid
const rules = computed(() => ({
  name: () =>
    textProblem(sensor.value.name, {
      max: NAME_MAX,
      message: `Escribe el nombre del sensor (máximo ${NAME_MAX} caracteres).`,
    }),
  ...(props.mode === "create" && {
    external_id: () => {
      const problem = textProblem(sensor.value.external_id, {
        max: EXTERNAL_ID_MAX,
        message: `Escribe la etiqueta del aparato (máximo ${EXTERNAL_ID_MAX} caracteres).`,
      });
      if (problem) return problem;
      const taken = props.takenLabels.find((label) =>
        sameLabel(label, sensor.value.external_id),
      );
      return taken
        ? `Ya hay un sensor con la etiqueta ${taken} en este edificio.`
        : null;
    },
  }),
  floor: () =>
    floorOptions.value.includes(sensor.value.floor)
      ? null
      : "Elige una planta de este edificio.",
  min_pressure: () => pressureProblem(sensor.value.min_pressure),
  // Cross-field rule (same as the model_validator of B3): the message goes
  // on the maximum, as in the mockup
  max_pressure: () => {
    const problem = pressureProblem(sensor.value.max_pressure);
    if (problem) return problem;
    const min = sensor.value.min_pressure;
    return !pressureProblem(min) && sensor.value.max_pressure <= min
      ? "El máximo debe ser mayor que el mínimo."
      : null;
  },
}));

// Checks every field, shows the messages and focuses the first wrong field.
// Returns true when the sensor can be sent to the API.
function validate() {
  if (check(rules.value)) return true;
  focusFirstError();
  return false;
}

// API errors of one field; the backend message says what is wrong
const API_ERRORS = {
  codes: {
    SENSOR_EXTERNAL_ID_TAKEN: "external_id",
    INVALID_NAME: "name",
    INVALID_THRESHOLDS: "max_pressure",
  },
  messages: {
    name: `Escribe el nombre del sensor (máximo ${NAME_MAX} caracteres).`,
    external_id: `Escribe la etiqueta del aparato (máximo ${EXTERNAL_ID_MAX} caracteres).`,
    floor: "Elige una planta de este edificio.",
    min_pressure: rangeMessage,
    max_pressure: rangeMessage,
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
