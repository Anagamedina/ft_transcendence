<template>
  <PublicLayout>
    <!-- Hero: light background, copy on the left, example building card on the right -->
    <section
      class="bg-gradient-to-b from-aqua-100 to-aqua-50 px-6 py-16 md:px-20 md:py-20"
    >
      <div
        class="max-w-6xl mx-auto grid gap-14 items-center md:grid-cols-[1.2fr_1fr]"
      >
        <!-- Left column: copy and call to action -->
        <div class="flex flex-col gap-5">
          <p class="text-xs font-bold uppercase tracking-widest text-aqua-600">
            Para edificios de Barcelona
          </p>
          <h1 class="text-4xl md:text-5xl font-bold leading-tight text-aqua-900">
            Detecta las fugas de agua antes de que sean un problema.
          </h1>
          <p class="text-lg text-slate-700 max-w-xl">
            AquaGuard vigila la presión del agua de tu edificio planta a planta
            y te avisa al momento si algo cambia.
          </p>
          <div class="flex flex-wrap items-center gap-3 mt-2">
            <RouterLink
              to="/prueba"
              class="bg-aqua-600 text-white font-semibold px-6 py-3.5 rounded-lg hover:bg-aqua-700 transition"
            >
              Empieza tu prueba gratis de 7 días
            </RouterLink>
            <span class="text-sm text-slate-600">
              Sin tarjeta · Te das de alta en 2 minutos
            </span>
          </div>
        </div>

        <!-- Right column: example building card (static data, no API call) -->
        <div
          class="bg-white border border-aqua-100 rounded-xl p-5 flex flex-col gap-4 shadow-[0_16px_40px_rgba(3,105,161,0.1)]"
        >
          <div class="flex justify-between items-center gap-3">
            <strong class="text-aqua-900">Hotel Diagonal Mar · Sant Martí</strong>
            <span
              class="px-3 py-1 rounded-full text-sm font-semibold bg-red-100 text-red-800"
            >
              1 alerta
            </span>
          </div>

          <ul class="flex flex-col gap-1.5" aria-label="Plantas del edificio de ejemplo">
            <li
              v-for="floor in exampleFloors"
              :key="floor.name"
              class="grid grid-cols-[90px_1fr] gap-2.5 items-center text-sm"
            >
              <span class="text-slate-600">{{ floor.name }}</span>
              <div
                class="flex items-center gap-2 px-2.5 py-2 rounded-lg text-slate-800"
                :class="statusStyles[floor.status].row"
              >
                <span
                  class="w-2.5 h-2.5 rounded-full"
                  :class="statusStyles[floor.status].dot"
                  aria-hidden="true"
                ></span>
                <span>{{ floor.point }} · {{ floor.pressure }} bar</span>
                <span class="sr-only">({{ statusStyles[floor.status].label }})</span>
              </div>
            </li>
          </ul>

          <p class="text-xs text-slate-500">Vista de ejemplo del panel del cliente.</p>
        </div>
      </div>
    </section>
  </PublicLayout>
</template>

<script setup>
import PublicLayout from "../../layouts/PublicLayout.vue";

// Illustrative data for the hero card (not from the API)
const exampleFloors = [
  { name: "Planta 3", point: "Montante", pressure: "4,2", status: "ok" },
  { name: "Planta 2", point: "Cocina", pressure: "1,1", status: "critical" },
  { name: "Planta 1", point: "Habitaciones", pressure: "4,4", status: "ok" },
  { name: "Planta baja", point: "Recepción", pressure: "3,0", status: "warning" },
  { name: "Sótano 1", point: "Bomba", pressure: "6,1", status: "ok" },
];

// Full class names so Tailwind can detect them at build time
const statusStyles = {
  ok: { row: "bg-green-50", dot: "bg-success", label: "normal" },
  warning: { row: "bg-amber-50", dot: "bg-warning", label: "aviso" },
  critical: { row: "bg-red-50", dot: "bg-danger", label: "alerta" },
};
</script>