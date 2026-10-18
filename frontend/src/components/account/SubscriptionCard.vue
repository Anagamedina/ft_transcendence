<template>
  <section
    class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm"
    aria-labelledby="subscription-title"
  >
    <h2 id="subscription-title" class="mb-4 text-lg font-bold text-gray-800">
      Suscripción
    </h2>

    <div v-if="organization" class="space-y-4">
      <div class="flex items-center justify-between gap-3">
        <span class="font-medium text-gray-800">{{ organization.name }}</span>
        <span
          class="rounded-full px-3 py-0.5 text-xs font-semibold"
          :class="status.pillClass"
          >{{ status.label }}</span
        >
      </div>

      <!-- Trial still running: progress bar and end date -->
      <template v-if="trial">
        <div
          class="h-2 rounded bg-gray-200"
          role="progressbar"
          :aria-valuenow="trial.day"
          aria-valuemin="0"
          :aria-valuemax="TRIAL_DAYS"
          :aria-label="`Día ${trial.day} de ${TRIAL_DAYS} de la prueba`"
        >
          <div
            class="h-2 rounded bg-aqua-600"
            :style="{ width: `${trial.percent}%` }"
          ></div>
        </div>
        <p class="text-sm text-gray-700">
          Día {{ trial.day }} de {{ TRIAL_DAYS }} · termina el
          <strong>{{ formatDate(organization.trial_ends_at) }}</strong
          >.
        </p>
        <p class="text-xs text-gray-500">
          Al terminar, tus datos quedan en solo lectura hasta que el equipo
          AquaGuard active la cuenta.
        </p>
      </template>

      <p v-else-if="status.trialEnded" class="text-sm text-gray-700">
        La prueba terminó el {{ formatDate(organization.trial_ends_at) }}. Tus
        datos están en solo lectura hasta que el equipo AquaGuard active la
        cuenta.
      </p>

      <p
        v-else-if="organization.status === 'ACTIVE'"
        class="text-sm text-gray-700"
      >
        Tu cuenta está activa.
      </p>

      <p
        v-else-if="organization.status === 'SUSPENDED'"
        class="text-sm text-gray-700"
      >
        Tu cuenta está suspendida. Escribe al equipo AquaGuard para reactivarla.
      </p>
    </div>

    <p v-else class="text-sm text-gray-500">
      No hay ninguna organización asociada a tu cuenta.
    </p>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { useAuthStore } from "../../stores/auth";
import { useClientStatus } from "../../composables/useClientStatus";
import { formatDate, parseDate } from "../../composables/useFormat";

// Length of the free trial (TRIAL_DAYS in the backend settings)
const TRIAL_DAYS = 7;
const DAY_MS = 24 * 60 * 60 * 1000;

const authStore = useAuthStore();
const organization = computed(() => authStore.organization);

// Same label and colors the admin sees for this client
const status = computed(() =>
  organization.value
    ? useClientStatus(organization.value)
    : { label: "", pillClass: "", trialEnded: false },
);

// Current day of a running trial (1..7) and the bar width; null if there is no running trial
const trial = computed(() => {
  const org = organization.value;
  if (!org || org.status !== "TRIAL" || status.value.trialEnded) return null;

  const end = parseDate(org.trial_ends_at);
  if (!end) return null;

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const endDay = new Date(end);
  endDay.setHours(0, 0, 0, 0);

  const daysLeft = Math.round((endDay - today) / DAY_MS);
  const day = Math.min(TRIAL_DAYS, Math.max(1, TRIAL_DAYS - daysLeft));
  return { day, percent: Math.round((day / TRIAL_DAYS) * 100) };
});
</script>
