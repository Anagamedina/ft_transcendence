<!--
  BUILDING DRAWING (F25)
  "Tu edificio" of the building page: the building drawn with its roof, its
  floors top to bottom, the street line and the basements under it. Each
  floor says how it is, with dot + text (never colour alone), worst first:
    revisar      pending alert (Sin atender)
    en curso     alert somebody is handling (En curso)
    sin conexión a sensor of the floor is offline
    a vigilar    a sensor out of range or near a limit, no alert yet
                 (utils/pressure.js, the same rule as "Mis edificios")
    todo bien    has sensors and nothing of the above
    sin sensor   no sensors
  Floors without sensors that follow each other are drawn as one row
  ("Plantas 1–5 · sin sensor"), so tall buildings with few sensors show
  what matters. Floors with sensors are buttons: the parent opens "Plantas
  y sensores" on that floor.
  With `show-sensors` (F26, "Plantas y sensores") it is the same drawing,
  same width, and each floor with sensors shows them as SensorPin in the
  same row (name + state on the left, pins on the right), so a 15-floor
  building with one sensor per floor stays compact. The pins are the
  buttons and emit "select-sensor" with the sensor id.
  Usage:
    <BuildingDrawing :floors="4" :basements="1" :sensors="sensors"
                     :states="{ 2: { pending: 1, inProgress: 0 } }"
                     @select="openFloor" />
    <BuildingDrawing ... show-sensors :selected-id="id"
                     @select-sensor="selectSensor" />
-->

<template>
  <div class="flex flex-col items-center">
    <!-- Roof -->
    <svg
      viewBox="0 0 100 12"
      preserveAspectRatio="none"
      class="h-8 w-full max-w-[300px]"
      aria-hidden="true"
    >
      <polygon points="0,12 50,0 100,12" :fill="aqua[800]" />
    </svg>

    <!-- Floors above the street -->
    <ol
      class="flex w-full max-w-[268px] flex-col gap-1 rounded-b bg-slate-200 p-1.5"
      :aria-label="`Plantas de ${name}`"
    >
      <li v-for="row in upperRows" :key="row.key">
        <FloorRow :row="row" />
      </li>
    </ol>

    <!-- Street line -->
    <div class="h-1 w-full max-w-[300px] bg-slate-600" aria-hidden="true"></div>

    <!-- Basements -->
    <ol
      v-if="basementRows.length"
      class="flex w-full max-w-[268px] flex-col gap-1 rounded-b-md bg-slate-200 p-1.5"
      :aria-label="`Sótanos de ${name}`"
    >
      <li v-for="row in basementRows" :key="row.key">
        <FloorRow :row="row" />
      </li>
    </ol>

    <SensorLegend v-if="showSensors" class="mt-3 max-w-[300px]" />
  </div>
</template>

<script setup>
import { computed, h } from "vue";
import { aqua } from "../theme/palette.js";
import { useLabels } from "../composables/useLabels";
import { floorLabel, floorRange } from "../utils/floors.js";
import { pressureState } from "../utils/pressure.js";
import SensorPin from "./SensorPin.vue";
import SensorLegend from "./SensorLegend.vue";

const props = defineProps({
  name: { type: String, default: "el edificio" },
  floors: { type: Number, default: 1 },
  basements: { type: Number, default: 0 },
  // { [floor]: { pending, inProgress } }
  states: { type: Object, default: () => ({}) },
  // SensorResponse list of the building
  sensors: { type: Array, default: () => [] },
  // "Plantas y sensores": also draw the sensors of each floor
  showSensors: { type: Boolean, default: false },
  // Sensor shown in the detail panel, to highlight its pin
  selectedId: { type: String, default: null },
});

const emit = defineEmits(["select", "select-sensor"]);

// { 3: [sensor, …], 0: […], -1: […] }
const sensorsByFloor = computed(() => {
  const groups = {};
  for (const sensor of props.sensors) {
    const floor = sensor.floor ?? 0;
    (groups[floor] ??= []).push(sensor);
  }
  return groups;
});

const { toneClasses } = useLabels();

// What a floor shows, worst first
function stateOf(floor) {
  const s = props.states[floor] ?? {};
  const onFloor = props.sensors.filter((sensor) => sensor.floor === floor);
  const keys = onFloor.map((sensor) => pressureState(sensor).key);
  const hasSensors = onFloor.length > 0;
  if (s.pending > 0)
    return { key: "pending", text: "revisar", tone: "danger", hasSensors };
  if (s.inProgress > 0)
    return { key: "inProgress", text: "en curso", tone: "info", hasSensors };
  if (keys.includes("offline"))
    return {
      key: "offline",
      text: "sin conexión",
      tone: "warning",
      hasSensors,
    };
  if (keys.includes("out") || keys.includes("near"))
    return { key: "watch", text: "a vigilar", tone: "warning", hasSensors };
  if (hasSensors)
    return { key: "ok", text: "todo bien", tone: "success", hasSensors };
  return { key: "none", text: "sin sensor", tone: "neutral", hasSensors };
}

// "Plantas 1–5", "Planta baja a planta 3", "Sótanos 1–2"
function rangeLabel(low, high) {
  if (low === high) return floorLabel(low);
  if (high < 0) return `Sótanos ${-high}–${-low}`;
  if (low === 0) return `Planta baja a planta ${high}`;
  return `Plantas ${low}–${high}`;
}

// Rows top to bottom; floors without sensors next to each other become one
function rowsOf(floorList) {
  const rows = [];
  for (const floor of floorList) {
    const state = stateOf(floor);
    const last = rows[rows.length - 1];
    if (state.key === "none" && last?.state.key === "none") {
      last.low = floor;
      last.label = rangeLabel(last.low, last.high);
      last.key = `${last.high}_${last.low}`;
      continue;
    }
    rows.push({
      key: `${floor}`,
      floor,
      high: floor,
      low: floor,
      label: floorLabel(floor),
      state,
    });
  }
  return rows;
}

const allFloors = computed(() => floorRange(props.floors, props.basements));
const upperRows = computed(() => rowsOf(allFloors.value.filter((f) => f >= 0)));
const basementRows = computed(() =>
  rowsOf(allFloors.value.filter((f) => f < 0)),
);

// One row: a button when its floor has sensors, plain text otherwise
const FloorRow = ({ row }) => {
  const { state } = row;
  const tone = toneClasses(state.tone);
  const strong = ["pending", "inProgress"].includes(state.key);
  const base =
    "flex w-full items-center justify-between gap-2 rounded px-3 py-2.5 text-left text-sm";
  const look = strong
    ? `${tone.pill} border ${tone.border} font-semibold`
    : row.floor < 0
      ? "bg-slate-50 text-slate-700"
      : "bg-white text-slate-700";
  const textClass = {
    ok: "text-success-dark",
    watch: "font-medium text-warning-dark",
    offline: "font-medium text-warning-dark",
    none: "text-slate-600",
  }[state.key];
  const children = [
    h("span", row.label),
    h("span", { class: "flex shrink-0 items-center gap-1.5" }, [
      state.key === "none"
        ? null
        : h("span", {
            class: `h-2.5 w-2.5 rounded-full ${tone.dot}`,
            "aria-hidden": "true",
          }),
      h("span", { class: textClass ?? "" }, state.text),
    ]),
  ];
  // Detailed drawing: one row with the floor and its state on the left and
  // the sensor pins on the right; the pins are the buttons
  if (props.showSensors && state.hasSensors) {
    const pins = (sensorsByFloor.value[row.floor] ?? []).map((sensor) =>
      h(SensorPin, {
        key: sensor.id,
        sensor,
        selected: sensor.id === props.selectedId,
        onSelect: (id) => emit("select-sensor", id),
      }),
    );
    return h(
      "div",
      { class: `${base} ${look} !py-1.5`, title: `${row.label}: ${state.text}` },
      [
        h("span", { class: "shrink-0 leading-tight" }, [
          h("span", { class: "block" }, row.label),
          h("span", { class: `block text-xs ${textClass ?? ""}` }, state.text),
        ]),
        h(
          "span",
          { class: "flex min-w-0 flex-wrap justify-end gap-1" },
          pins,
        ),
      ],
    );
  }
  if (!state.hasSensors)
    return h("div", { class: `${base} ${look}` }, children);
  return h(
    "button",
    {
      type: "button",
      class: `${base} ${look} hover:ring-2 hover:ring-aqua-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-aqua-600`,
      onClick: () => emit("select", row.floor),
    },
    children,
  );
};
FloorRow.props = ["row"];
</script>
