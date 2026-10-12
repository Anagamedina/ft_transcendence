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
              class="shrink-0 whitespace-nowrap px-3 py-1 rounded-full text-sm font-semibold bg-red-100 text-red-800"
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

    <!-- How it works: three steps -->
    <section id="metodo" class="bg-aqua-50 px-6 py-14 md:px-20">
      <div class="max-w-6xl mx-auto flex flex-col gap-7">
        <h2 class="text-3xl font-bold text-aqua-900 text-center">Cómo funciona</h2>
        <ol class="grid gap-5 md:grid-cols-3">
          <li
            v-for="(step, index) in howItWorks"
            :key="step.title"
            class="bg-white border border-aqua-100 rounded-xl p-6 flex flex-col gap-2"
          >
            <p class="text-xs font-bold uppercase tracking-widest text-aqua-600">
              Paso {{ index + 1 }}
            </p>
            <h3 class="text-lg font-bold text-aqua-900">{{ step.title }}</h3>
            <p class="text-slate-600">{{ step.text }}</p>
          </li>
        </ol>
      </div>
    </section>

    <!-- Coverage: the ten districts of Barcelona -->
    <section id="cobertura" class="bg-aqua-50 px-6 pt-2 pb-14 md:px-20">
      <div class="max-w-6xl mx-auto grid gap-10 items-center md:grid-cols-2">
        <div class="flex flex-col gap-3">
          <h2 class="text-3xl font-bold text-aqua-900">
            Damos servicio en los 10 distritos de Barcelona
          </h2>
          <p class="text-slate-600">
            Nuestro equipo técnico trabaja solo en la ciudad, así que llegamos
            rápido cuando hay una alerta.
          </p>
        </div>
        <ul class="grid grid-cols-2 gap-2" aria-label="Distritos">
          <li
            v-for="district in districts"
            :key="district"
            class="bg-white border border-aqua-100 rounded-xl px-3.5 py-2.5 flex items-center gap-2.5 text-sm"
          >
            <span class="w-2 h-2 rounded-full bg-aqua-400" aria-hidden="true"></span>
            {{ district }}
          </li>
        </ul>
      </div>
    </section>

    <!-- Alert lifecycle: active, acknowledged, resolved -->
    <section id="alertas" class="bg-aqua-50 px-6 pb-14 md:px-20">
      <div
        class="max-w-6xl mx-auto bg-white border border-aqua-100 rounded-xl p-7 grid gap-8 items-center md:grid-cols-[1fr_1.3fr]"
      >
        <div class="flex flex-col gap-2">
          <h2 class="text-2xl font-bold text-aqua-900">Alertas que se cierran</h2>
          <p class="text-slate-600">
            Cada alerta pasa por tres estados y queda registrado quién actuó y
            cuánto tardó.
          </p>
        </div>
        <ol class="flex flex-wrap items-center gap-2.5" aria-label="Estados de una alerta">
          <li class="flex items-center gap-2.5">
            <span class="px-3 py-1 rounded-full text-sm font-semibold bg-red-100 text-red-800">
              Activa
            </span>
            <span class="text-slate-500" aria-hidden="true">→</span>
          </li>
          <li class="flex items-center gap-2.5">
            <span class="px-3 py-1 rounded-full text-sm font-semibold bg-amber-100 text-amber-800">
              Reconocida
            </span>
            <span class="text-slate-500" aria-hidden="true">→</span>
          </li>
          <li>
            <span class="px-3 py-1 rounded-full text-sm font-semibold bg-emerald-100 text-emerald-800">
              Resuelta
            </span>
          </li>
        </ol>
      </div>
    </section>

    <!-- Roles: what the AquaGuard team and the client can do -->
    <section id="roles" class="bg-white px-6 py-14 md:px-20">
      <div class="max-w-3xl mx-auto flex flex-col gap-6">
        <h2 class="text-3xl font-bold text-aqua-900 text-center">Quién puede hacer qué</h2>
        <div class="overflow-x-auto border border-slate-200 rounded-xl">
          <table class="w-full text-left text-sm sm:text-base">
            <thead class="bg-aqua-50 text-aqua-800">
              <tr>
                <th scope="col" class="px-3 sm:px-4 py-3">Acción</th>
                <th scope="col" class="px-3 sm:px-4 py-3 text-center">Equipo AquaGuard</th>
                <th scope="col" class="px-3 sm:px-4 py-3 text-center">Cliente</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="permission in permissions"
                :key="permission.action"
                class="border-t border-slate-200"
              >
                <th scope="row" class="px-3 sm:px-4 py-3 font-normal">{{ permission.action }}</th>
                <td class="px-3 sm:px-4 py-3 text-center">{{ permission.team }}</td>
                <td class="px-3 sm:px-4 py-3 text-center">{{ permission.client }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Final call to action -->
    <section class="bg-aqua-50 px-6 py-14 md:px-20 text-center flex flex-col items-center gap-4">
      <div class="water-drop mb-4" aria-hidden="true"></div>
      <h2 class="text-3xl font-bold text-aqua-900">¿Tu edificio está en Barcelona?</h2>
      <p class="text-slate-600">Pruébalo 7 días gratis. Si te convence, activamos tu cuenta.</p>
      <RouterLink
        to="/prueba"
        class="bg-aqua-600 text-white font-semibold px-6 py-3.5 rounded-lg hover:bg-aqua-700 transition"
      >
        Empezar la prueba
      </RouterLink>
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

// Steps shown in the "How it works" section
const howItWorks = [
  {
    title: "Te registras y pruebas gratis",
    text: "Creas tu cuenta, eliges el distrito de tu edificio y empiezas 7 días de prueba.",
  },
  {
    title: "Instalamos sensores por planta",
    text: "Un sensor de presión en cada punto crítico, de los sótanos a la cubierta.",
  },
  {
    title: "Te avisamos al momento",
    text: "Si la presión sale de su rango (0–25 bar), se abre una alerta en tu panel.",
  },
];

// Barcelona districts covered by the service
const districts = [
  "Ciutat Vella",
  "Eixample",
  "Sants-Montjuïc",
  "Les Corts",
  "Sarrià-Sant Gervasi",
  "Gràcia",
  "Horta-Guinardó",
  "Nou Barris",
  "Sant Andreu",
  "Sant Martí",
];

// Permissions table shown in the "Who can do what" section
const permissions = [
  { action: "Dar de alta clientes, edificios y sensores", team: "Sí", client: "—" },
  { action: "Ajustar los umbrales de presión", team: "Sí", client: "—" },
  { action: "Invitar usuarios a una organización", team: "Sí", client: "—" },
  { action: "Ver edificios, sensores y lecturas", team: "Todos", client: "Los suyos" },
  { action: "Reconocer y resolver alertas", team: "Sí", client: "Sí" },
  { action: "Subir y descargar documentos", team: "Sí", client: "Sí" },
];
</script>

<style scoped>
/* Decorative floating drop for the final call to action */
.water-drop {
  width: 96px;
  height: 96px;
  background: linear-gradient(135deg, #ffffff 0%, #a5f3fc 45%, #0369a1 100%);
  border-radius: 50% 50% 50% 0;
  transform: rotate(135deg);
  box-shadow:
    inset -6px -6px 14px rgba(255, 255, 255, 0.4),
    6px 6px 18px rgba(3, 105, 161, 0.3);
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%,
  100% {
    transform: rotate(135deg) translateY(0);
  }
  50% {
    transform: rotate(135deg) translateY(-10px);
  }
}

/* Respect users who disable animations in their system settings */
@media (prefers-reduced-motion: reduce) {
  .water-drop {
    animation: none;
  }
}
</style>