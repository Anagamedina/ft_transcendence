<!--
  MISSING FLOORS LIST (#283)
  Tab "Plantas sin sensor": the plan includes one sensor per floor, so for
  each building with floors that have none, which ones and how many are
  covered. "+ Instalar aquí" opens the form with that building and its first
  missing floor already chosen.
-->

<template>
  <div class="overflow-hidden rounded-xl border border-slate-200 bg-white">
    <ul class="divide-y divide-slate-100">
      <li
        v-for="row in rows"
        :key="row.site.id"
        class="flex flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3.5 text-sm"
      >
        <div class="min-w-[12rem] flex-1">
          <p class="font-medium text-slate-900">{{ row.site.organization_name }}</p>
          <p class="text-xs text-slate-500">{{ row.site.name }}</p>
        </div>
        <div class="min-w-[12rem] flex-1">
          <p class="font-semibold text-amber-700">
            {{ row.missing.length }} {{ row.missing.length === 1 ? "planta" : "plantas" }} sin sensor
          </p>
          <p class="text-xs text-slate-500">{{ row.missing.map(floorLabel).join(", ") }}</p>
        </div>
        <p class="whitespace-nowrap text-[13px] text-slate-600">{{ row.covered }} de {{ row.total }} con sensor</p>
        <button
          type="button"
          class="h-9 rounded-lg border border-slate-300 bg-white px-3 text-[13px] font-semibold text-slate-900 hover:border-aqua-400"
          @click="$emit('install', { site: row.site, floor: row.missing[0] })"
        >
          + Instalar aquí
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { floorLabel } from "../../utils/floors";

defineProps({
  // floorsWithoutSensor(sites, sensors)
  rows: { type: Array, default: () => [] },
});

defineEmits(["install"]);
</script>
