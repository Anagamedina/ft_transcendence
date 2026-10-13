<!--
  BUILDING STACK
  Building floor by floor (F4), as in the C-Edificio mockup: one row per floor
  from the top floor down to the ground floor, the "Nivel de calle" line, and
  the basements below. Each floor shows its sensors as SensorPin.
  Pure visual component: it receives the building and its sensors already
  loaded and emits "select" with the sensor id; it never calls the API.
  The page around it (title, address, back link) belongs to the view.
  Shapes: floors / basements from SiteResponse (B2),
          sensors = SensorResponse[] (B3: floor, health).
  Usage:
    <BuildingStack
      :name="site.name" :floors="site.floors" :basements="site.basements"
      :sensors="sensors" :selected-id="selectedId" @select="selectedId = $event" />
-->

<template>
  <section
    class="flex flex-col gap-1.5 rounded-xl border border-slate-200 bg-white p-[18px]"
    :aria-label="`${name}: edificio planta a planta`"
  >
    <EmptyState
      v-if="!sensors.length"
      icon="building"
      title="Este edificio todavía no tiene sensores"
      message="Cuando se instale un sensor, aparecerá en su planta."
      compact
    />

    <template v-else>
      <template v-for="floor in floorList" :key="floor">
        <!-- Street level, between the ground floor and the first basement -->
        <div
          v-if="floor === -1"
          class="my-1 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.08em] text-slate-500"
        >
          <span class="h-0.5 flex-grow bg-slate-400" aria-hidden="true"></span>
          Nivel de calle
          <span class="h-0.5 flex-grow bg-slate-400" aria-hidden="true"></span>
        </div>

        <div
          class="grid grid-cols-[96px_minmax(0,1fr)] items-center gap-2.5 rounded-lg px-3 py-2.5"
          :class="floor < 0 ? 'bg-slate-100' : 'bg-slate-50'"
        >
          <span class="text-[13px] font-semibold text-slate-700">{{ floorLabel(floor) }}</span>
          <div class="flex flex-wrap gap-1.5">
            <SensorPin
              v-for="sensor in sensorsByFloor[floor] || []"
              :key="sensor.id"
              :sensor="sensor"
              :selected="sensor.id === selectedId"
              @select="$emit('select', $event)"
            />
            <span v-if="!sensorsByFloor[floor]" class="text-xs text-slate-400">Sin sensores</span>
          </div>
        </div>
      </template>

      <!-- Sensors whose floor is outside the building (should not happen: B3 validates it) -->
      <p v-if="outOfRange.length" class="text-xs text-warning-dark">
        {{ outOfRange.length }} sensor(es) en una planta que no existe en este edificio.
      </p>

      <SensorLegend v-if="showLegend" class="mt-2" />
    </template>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import EmptyState from './EmptyState.vue'
import SensorPin from './SensorPin.vue'
import SensorLegend from './SensorLegend.vue'
import { floorLabel, floorRange } from '../utils/floors'

const props = defineProps({
  // Building name, used by screen readers to name the section
  name: { type: String, required: true },
  // Floors above ground, ground floor included (B2). Minimum 1.
  floors: { type: Number, default: 1 },
  basements: { type: Number, default: 0 },
  // SensorResponse[] of this building
  sensors: { type: Array, default: () => [] },
  // Id of the sensor shown in the detail panel, to highlight its pin
  selectedId: { type: String, default: null },
  showLegend: { type: Boolean, default: true },
})

defineEmits(['select'])

const floorList = computed(() => floorRange(props.floors, props.basements))

// { 3: [sensor, …], 0: […], -1: […] }
const sensorsByFloor = computed(() => {
  const groups = {}
  for (const sensor of props.sensors) {
    const floor = sensor.floor ?? 0
    if (!groups[floor]) groups[floor] = []
    groups[floor].push(sensor)
  }
  return groups
})

const outOfRange = computed(() =>
  props.sensors.filter((s) => !floorList.value.includes(s.floor ?? 0)),
)
</script>
