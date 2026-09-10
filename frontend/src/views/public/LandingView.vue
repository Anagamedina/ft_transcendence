<template>
  <PublicLayout>
    <section
      class="bg-gradient-to-r from-[#0369A1] to-[#06B6D4] text-white px-6 flex-1 flex items-center relative pb-32 md:pb-24"
    >
      <div
        class="max-w-6xl mx-auto grid md:grid-cols-[auto_1fr] gap-10 items-center text-center md:text-left"
      >
        <div
          class="order-2 md:order-1 flex justify-center md:justify-start mb-8 md:mb-0"
        >
          <div class="water-drop-lg scale-75 md:scale-100"></div>
        </div>

        <div class="order-1 md:order-2">
          <h1 class="text-4xl md:text-5xl font-bold leading-tight">
            Detecta las fugas de agua
            <br />
            antes de que sean un problema.
          </h1>

          <p class="mt-4 text-lg text-white/90 drop-shadow">
            AquaGuard monitoriza en tiempo real los sensores de presión de tu
            edificio y te alerta al instante ante cualquier anomalía.
          </p>

          <RouterLink
            to="/registro"
            class="inline-block mt-8 bg-white text-[#0369A1] font-semibold px-8 py-3 rounded-lg hover:bg-gray-100 transition"
          >
            Comenzar ahora
          </RouterLink>
        </div>
      </div>

      <svg
        class="absolute bottom-0 left-0 w-full pointer-events-none"
        viewBox="0 0 1440 100"
        preserveAspectRatio="none"
        style="height: 190px; transform: translateY(1px)"
      >
        <path
          fill="#0F172A"
          d="M0,50 C360,100 1080,0 1440,50 L1440,100 L0,100 Z"
        ></path>
      </svg>
    </section>

    <section class="bg-[#0F172A] py-0 px-6">
      <div class="max-w-6xl mx-auto">
        <h2 class="text-3xl font-bold text-center text-white mb-8">
          Cada gota, bajo control
        </h2>
        <div
          class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 justify-items-center"
        >
          <Card
            title="Detección en tiempo real"
            description="Enterarte de una fuga el mismo día, no meses después."
            :show-button="false"
          >
            <template #icon>
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="w-full h-full"
                aria-hidden="true"
              >
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
            </template>
          </Card>

          <Card
            title="Panel de control centralizado"
            description="Ver de un vistazo el estado de todos tus puntos de agua."
            :show-button="false"
          >
            <template #icon>
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="w-full h-full"
                aria-hidden="true"
              >
                <line x1="4" y1="20" x2="4" y2="10" />
                <line x1="12" y1="20" x2="12" y2="4" />
                <line x1="20" y1="20" x2="20" y2="14" />
              </svg>
            </template>
          </Card>

          <Card
            title="Alertas instantáneas"
            description="Recibir avisos donde estés, sin depender de estar delante de una pantalla."
            :show-button="false"
          >
            <template #icon>
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="w-full h-full"
                aria-hidden="true"
              >
                <path
                  d="M6 8a6 6 0 0 1 12 0c0 4 1.5 5.5 2 6H4c0.5-0.5 2-2 2-6z"
                />
                <path d="M9.5 18a2.5 2.5 0 0 0 5 0" />
              </svg>
            </template>
          </Card>

          <Card
            title="Histórico y estadísticas"
            description="Datos claros para tomar decisiones, no solo números sueltos."
            :show-button="false"
          >
            <template #icon>
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="w-full h-full"
                aria-hidden="true"
              >
                <polyline points="3 17 9 11 13 15 21 6" />
                <polyline points="15 6 21 6 21 12" />
              </svg>
            </template>
          </Card>
        </div>
      </div>
    </section>
  </PublicLayout>
</template>

<script setup>
import PublicLayout from "../../layouts/PublicLayout.vue";
import Card from "../../components/Card.vue";
</script>

<style scoped>
.water-drop-lg {
  width: 180px;
  height: 180px;
  background: linear-gradient(135deg, #ffffff 0%, #a5f3fc 45%, #0369a1 100%);
  border-radius: 50% 50% 50% 0;
  transform: rotate(135deg);
  box-shadow:
    inset -8px -8px 20px rgba(255, 255, 255, 0.4),
    8px 8px 25px rgba(3, 105, 161, 0.4);
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%,
  100% {
    transform: rotate(135deg) translateY(0);
  }
  50% {
    transform: rotate(135deg) translateY(-12px);
  }
}
</style>
