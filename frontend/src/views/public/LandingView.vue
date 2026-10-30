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
          <h1
            class="text-4xl md:text-5xl font-bold leading-tight text-aqua-900"
          >
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

        <!-- Right column: example building with the same drawing as the
             client panel (BuildingDrawing, static data, no API call) -->
        <figure
          class="bg-white border border-aqua-100 rounded-xl p-5 flex flex-col gap-4 shadow-[0_16px_40px_theme(colors.aqua.600/10%)]"
        >
          <div class="flex justify-between items-center gap-3">
            <strong class="text-aqua-900">Tu edificio</strong>
            <span
              class="shrink-0 whitespace-nowrap px-3 py-1 rounded-full text-sm font-semibold"
              :class="toneClasses(tone('AlertState', 'ACTIVE')).pill"
            >
              1 sin atender
            </span>
          </div>

          <!-- inert: in the panel the sensors open their detail; here they are
               only a picture, so they cannot be clicked or focused -->
          <div inert>
            <BuildingDrawing
              name="el edificio de ejemplo"
              :floors="exampleBuilding.floors"
              :basements="exampleBuilding.basements"
              :sensors="exampleBuilding.sensors"
              :states="exampleBuilding.states"
              show-sensors
            />
          </div>

          <figcaption class="text-xs text-slate-600">
            Vista de ejemplo del panel del cliente: la planta 2 está para
            «revisar» porque tiene una alerta sin atender, y la planta baja,
            «a vigilar» porque su presión está cerca del mínimo.
          </figcaption>
        </figure>
      </div>
    </section>

    <!-- How it works: three steps -->
    <section id="metodo" class="bg-aqua-50 px-6 py-14 md:px-20">
      <div class="max-w-6xl mx-auto flex flex-col gap-7">
        <h2 class="text-3xl font-bold text-aqua-900 text-center">
          Cómo funciona
        </h2>
        <ol class="grid gap-5 md:grid-cols-3">
          <li
            v-for="(step, index) in howItWorks"
            :key="step.title"
            class="bg-white border border-aqua-100 rounded-xl p-6 flex flex-col gap-2"
          >
            <p
              class="text-xs font-bold uppercase tracking-widest text-aqua-600"
            >
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
            <span
              class="w-2 h-2 rounded-full bg-aqua-400"
              aria-hidden="true"
            ></span>
            {{ district }}
          </li>
        </ul>
      </div>
    </section>

    <!-- Alert lifecycle (F28): AquaGuard warns, the client fixes, the
         readings confirm. Same states and colours as the panels (useLabels). -->
    <section id="alertas" class="bg-aqua-50 px-6 pb-14 md:px-20">
      <div
        class="max-w-6xl mx-auto bg-white border border-aqua-100 rounded-xl p-7 flex flex-col gap-6"
      >
        <div class="flex flex-col gap-2">
          <h2 class="text-2xl font-bold text-aqua-900">
            Así funciona una alerta
          </h2>
          <p class="text-slate-600">
            Te avisamos, tú lo arreglas y las lecturas confirman que ya va bien.
          </p>
        </div>
        <ol class="grid gap-4 md:grid-cols-3" aria-label="Estados de una alerta">
          <li
            v-for="(step, index) in alertSteps"
            :key="step.state"
            class="flex flex-col gap-2 rounded-xl border border-slate-200 p-5"
          >
            <!-- The state is written out, not only shown by its colour -->
            <span
              class="self-start rounded-full px-3 py-1 text-sm font-semibold"
              :class="toneClasses(tone('AlertState', step.state)).pill"
            >
              {{ index + 1 }}. {{ label("AlertState", step.state) }}
            </span>
            <h3 class="text-lg font-bold text-aqua-900">{{ step.title }}</h3>
            <p class="text-slate-600">{{ step.text }}</p>
          </li>
        </ol>
      </div>
    </section>

    <!-- Roles: what the AquaGuard team and the client can do -->
    <section id="roles" class="bg-white px-6 py-14 md:px-20">
      <div class="max-w-3xl mx-auto flex flex-col gap-6">
        <h2 class="text-3xl font-bold text-aqua-900 text-center">
          Quién puede hacer qué
        </h2>
        <div class="overflow-x-auto border border-slate-200 rounded-xl">
          <table class="w-full text-left text-sm sm:text-base">
            <thead class="bg-aqua-50 text-aqua-800">
              <tr>
                <th scope="col" class="px-3 sm:px-4 py-3">Acción</th>
                <th scope="col" class="px-3 sm:px-4 py-3 text-center">
                  Equipo AquaGuard
                </th>
                <th scope="col" class="px-3 sm:px-4 py-3 text-center">
                  Cliente
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="permission in permissions"
                :key="permission.action"
                class="border-t border-slate-200"
              >
                <th scope="row" class="px-3 sm:px-4 py-3 font-normal">
                  {{ permission.action }}
                </th>
                <td class="px-3 sm:px-4 py-3 text-center">
                  {{ permission.team }}
                </td>
                <td class="px-3 sm:px-4 py-3 text-center">
                  {{ permission.client }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="text-sm text-slate-600 text-center">
          AquaGuard da la alerta por arreglada cuando la presión lleva 15
          minutos normal. Solo la cierra a mano si las lecturas no pueden
          confirmarlo, por ejemplo al cambiar un sensor.
        </p>
      </div>
    </section>


  <!-- Pricing -->
  <section id="precios" class="bg-aqua-50 px-6 py-16 md:px-20">
    <div class="max-w-6xl mx-auto flex flex-col gap-10">
      <div class="text-center flex flex-col gap-3">
        <p class="text-xs font-bold uppercase tracking-widest text-aqua-600">
          Precios transparentes
        </p>
        <h2 class="text-3xl md:text-4xl font-bold text-aqua-900">
          Un plan para cada edificio
        </h2>
        <p class="text-slate-600 max-w-2xl mx-auto">
          Elige tu plan según el número de edificios. Añade los sensores que
          necesites y empieza con 7 días de prueba gratis.
        </p>
      </div>

      <div class="grid gap-6 md:grid-cols-3 items-stretch">
        <article
          v-for="plan in plans"
          :key="plan.name"
          class="relative bg-white border rounded-2xl p-7 flex flex-col gap-6 transition hover:-translate-y-1 hover:shadow-lg"
          :class="plan.featured
            ? 'border-aqua-500 shadow-md ring-1 ring-aqua-500'
            : 'border-aqua-100'"
        >
          <span
            v-if="plan.featured"
            class="absolute -top-3 left-1/2 -translate-x-1/2 bg-aqua-600 text-white text-xs font-bold px-3 py-1 rounded-full whitespace-nowrap"
          >
            Más elegido
          </span>

          <div>
            <h3 class="text-xl font-bold text-aqua-900">{{ plan.name }}</h3>
            <p class="text-sm text-slate-600 mt-1">{{ plan.description }}</p>
          </div>

          <div>
            <p class="flex items-baseline gap-1">
              <span class="text-4xl font-bold text-aqua-900">
                {{ plan.price }} €
              </span>
              <span class="text-slate-600 text-sm">/ mes</span>
            </p>
            <p class="text-sm text-slate-500 mt-2">
              {{ plan.range }} edificios
            </p>
            <p class="text-sm text-slate-500">
              + 10 €/sensor/mes · IVA no incluido
            </p>
          </div>

          <ul class="flex flex-col gap-3 text-sm text-slate-700">
            <li v-for="feature in plan.features" :key="feature"
                class="flex gap-2">
              <span class="text-aqua-600 font-bold" aria-hidden="true">✓</span>
              <span>{{ feature }}</span>
            </li>
          </ul>

          <RouterLink
            to="/prueba"
            class="mt-auto block text-center font-semibold px-5 py-3 rounded-lg transition"
            :class="plan.featured
              ? 'bg-aqua-600 text-white hover:bg-aqua-700'
              : 'border border-aqua-200 text-aqua-800 hover:bg-aqua-50'"
          >
            Empezar prueba gratis
          </RouterLink>
        </article>
      </div>

      <p class="text-sm text-slate-600 text-center">
        Pago mensual sin permanencia o anual por adelantado (equivalente a
        10 meses). La prueba dura 7 días, sin tarjeta ni compromiso.
      </p>
    </div>
  </section>

    <!-- Final call to action -->
    <section
      class="bg-aqua-50 px-6 py-14 md:px-20 text-center flex flex-col items-center gap-4"
    >
      <AppLogo icon-only size="xl" class="floating-drop mb-4" />
      <h2 class="text-3xl font-bold text-aqua-900">
        ¿Tu edificio está en Barcelona?
      </h2>
      <p class="text-slate-600">
        Pruébalo 7 días gratis. Si te convence, te haces cliente desde tu panel.
      </p>
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
import AppLogo from "../../components/AppLogo.vue";
import BuildingDrawing from "../../components/BuildingDrawing.vue";
import { useLabels } from "../../composables/useLabels";

// Alert states with the panels' own texts and colours (F28)
const { label, tone, toneClasses } = useLabels();

// "Así funciona una alerta": the same flow the client sees in the panel
// (notices #275, "Me encargo" #252, closing by the readings #277)
const alertSteps = [
  {
    state: "ACTIVE",
    title: "AquaGuard te avisa",
    text: "Se abre una alerta en tu panel. Si nadie se encarga, te avisamos por email y, si es crítica y sigue sin respuesta, te llamamos.",
  },
  {
    state: "ACKNOWLEDGED",
    title: "Tú lo arreglas",
    text: "Pulsas «Me encargo»: tu equipo sabe que alguien se ocupa y dejamos de insistir.",
  },
  {
    state: "RESOLVED",
    title: "Las lecturas lo confirman",
    text: "Cuando la presión vuelve a lo normal durante 15 minutos, la alerta se cierra sola. Queda registrado quién se encargó y cuánto tardó.",
  },
];

// Illustrative building for the hero (not from the API). Same shapes as the
// API: floors counts the ground floor (4 = ground floor to floor 3) and each
// sensor is a SensorResponse with the fields BuildingDrawing and SensorPin read
const exampleSensor = (id, name, floor, value, health) => ({
  id: `demo-${id}`,
  name,
  floor,
  last_value: value,
  min_pressure: 2,
  max_pressure: 6.5,
  unit: "bar",
  status: "ACTIVE",
  health,
});

const exampleBuilding = {
  floors: 4,
  basements: 1,
  sensors: [
    exampleSensor(1, "Montante", 3, 4.2, "OK"),
    exampleSensor(2, "Cocina", 2, 1.1, "CRITICAL"),
    exampleSensor(3, "Habitaciones", 1, 4.4, "OK"),
    // Inside its range (2–6,5) but close to the minimum: "a vigilar", no alert
    exampleSensor(4, "Recepción", 0, 2.3, "OK"),
    exampleSensor(5, "Bomba", -1, 4.8, "OK"),
  ],
  // Floor 2 has an alert nobody has taken yet: "revisar"
  states: { 2: { pending: 1, inProgress: 0 } },
};


// Steps shown in the "How it works" section
const howItWorks = [
  {
    title: "Te registras y pruebas gratis",
    text: "Creas tu cuenta y empiezas 7 días de prueba, sin tarjeta.",
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
  {
    action: "Dar de alta clientes, edificios y sensores",
    team: "Sí",
    client: "—",
  },
  { action: "Ajustar los umbrales de presión", team: "Sí", client: "—" },
  { action: "Invitar usuarios a una organización", team: "Sí", client: "—" },
  {
    action: "Ver edificios, sensores y lecturas",
    team: "Todos",
    client: "Los suyos",
  },
  // F28: the client takes charge; the readings close the alert, and
  // AquaGuard closes it by hand only when they cannot confirm it.
  { action: "Encargarse de una alerta («Me encargo»)", team: "—", client: "Sí" },
  {
    action: "Avisar si nadie se encarga (email y llamada)",
    team: "Sí",
    client: "—",
  },
  {
    action: "Dar una alerta por arreglada",
    team: "Sí (con las lecturas)",
    client: "—",
  },
  { action: "Subir y descargar documentos", team: "Sí", client: "Sí" },
];

// Pricing plans
const plans = [
  {
    name: "Básico",
    description: "Para edificios pequeños",
    price: 29,
    range: "1–5",
    featured: false,
    features: [
      "De 1 a 5 edificios",
      "Monitorización de presión",
      "Alertas en tiempo real",
      "Panel de control y documentos",
    ],
  },
  {
    name: "Profesional",
    description: "Para organizaciones en crecimiento",
    price: 79,
    range: "6–10",
    featured: true,
    features: [
      "De 6 a 10 edificios",
      "Monitorización de presión",
      "Alertas en tiempo real",
      "Panel de control y documentos",
    ],
  },
  {
    name: "Empresa",
    description: "Para grandes organizaciones",
    price: 199,
    range: "11–20",
    featured: false,
    features: [
      "De 11 a 20 edificios",
      "Monitorización de presión",
      "Alertas en tiempo real",
      "Panel de control y documentos",
    ],
  },
];

</script>

<style scoped>
/* Decorative floating drop for the final call to action (same drop as
   the logo, AppLogo) */
.floating-drop {
  filter: drop-shadow(6px 6px 12px rgb(3 105 161 / 0.3));
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

/* Respect users who disable animations in their system settings */
@media (prefers-reduced-motion: reduce) {
  .floating-drop {
    animation: none;
  }
}
</style>
