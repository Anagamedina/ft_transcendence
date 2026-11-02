<!--
  TRIAL BANNER
  Notice above the client pages while the organization is on the free trial
  (B10): days left, or the read-only notice once it has expired (B12), with a
  "Hazte cliente" link to /app/subscribe (B14).
  Same rule as the backend (organizations/trial.py): the trial expires at the
  exact instant of `trial_ends_at`, and only a TRIAL organization can expire.
  Renders nothing for ACTIVE organizations or without an organization.
  Usage:
    <TrialBanner :organization="authStore.organization" />
-->

<template>
  <div
    v-if="state === 'expired'"
    class="border-b border-danger/40 bg-danger-light px-6 py-3 text-sm text-danger-dark"
    role="status"
  >
    <strong>Tu periodo de prueba ha terminado.</strong>
    Puedes consultar tus datos, pero no modificarlos hasta que te hagas cliente
    o AquaGuard amplíe la prueba.
    <RouterLink :to="SUBSCRIBE_PATH" :class="LINK_CLASS"
      >Hazte cliente</RouterLink
    >
  </div>

  <div
    v-else-if="state === 'trial'"
    class="border-b border-warning/40 bg-warning-light px-6 py-3 text-sm text-warning-dark"
    role="status"
  >
    <strong>Periodo de prueba:</strong>
    <template v-if="daysLeft > 1"> quedan {{ daysLeft }} días.</template>
    <template v-else-if="daysLeft === 1"> queda 1 día.</template>
    <template v-else> la prueba termina hoy.</template>
    <RouterLink :to="SUBSCRIBE_PATH" :class="LINK_CLASS"
      >Hazte cliente</RouterLink
    >
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  // OrganizationSummary from /api/users/me: { status, trial_ends_at }
  organization: { type: Object, default: null },
  // Injected in tests; the banner is re-evaluated whenever the props change
  now: { type: Date, default: null },
});

const DAY_MS = 24 * 60 * 60 * 1000;

// "Hazte cliente" (B14): the subscribe page of the client area
const SUBSCRIBE_PATH = "/app/subscribe";
const LINK_CLASS = "ml-2 font-semibold underline hover:no-underline";

const trialEnd = computed(() => {
  const organization = props.organization;
  if (organization?.status !== "TRIAL" || !organization.trial_ends_at)
    return null;
  const end = new Date(organization.trial_ends_at);
  return Number.isNaN(end.getTime()) ? null : end;
});

// null | 'trial' | 'expired'
const state = computed(() => {
  if (!trialEnd.value) return null;
  const now = props.now ?? new Date();
  return trialEnd.value <= now ? "expired" : "trial";
});

// Calendar days until the end, so "termina hoy" on its last day
const daysLeft = computed(() => {
  if (!trialEnd.value) return null;
  const today = new Date(props.now ?? new Date());
  const end = new Date(trialEnd.value);
  today.setHours(0, 0, 0, 0);
  end.setHours(0, 0, 0, 0);
  return Math.max(0, Math.round((end - today) / DAY_MS));
});
</script>
