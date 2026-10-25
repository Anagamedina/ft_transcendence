<!--
  ALERT DETAIL PANEL (#252, option A of the canvas
  https://claude.ai/artifact/9pWxLtDY5NHkPLCssUzYYv)
  Short side panel: the reading and its limit in the title, where, who is
  on it, "Llamar" / "Email" to the client,
  and "Ver sensor" at the bottom. The readings close the alert (#277):
  "Cerrar a mano…" is a discreet link for the exceptions, with its
  confirmation inside the panel. Esc closes; Tab stays inside the panel.
-->

<template>
  <Teleport to="body">
    <!-- z-[70]: above the mobile menu button of the Sidebar (z-[60]) -->
    <div v-if="alert" class="fixed inset-0 z-[70] flex justify-end">
      <div class="absolute inset-0 bg-slate-900/30" aria-hidden="true" @click="close"></div>

      <aside
        ref="panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="alert-detail-title"
        class="relative flex h-full w-full max-w-md flex-col overflow-y-auto bg-white shadow-xl"
        @keydown.esc.prevent="close"
        @keydown.tab="trapFocus"
      >
        <header class="flex flex-col gap-1.5 border-b border-slate-200 px-5 pb-4 pt-4">
          <div class="flex items-center gap-2">
            <span
              class="rounded-full px-2 py-0.5 text-xs font-bold"
              :class="
                alert.severity === 'CRITICAL'
                  ? 'bg-rose-50 text-rose-700'
                  : 'bg-amber-50 text-amber-800'
              "
              :title="help('AlertSeverity', alert.severity)"
            >
              {{ label("AlertSeverity", alert.severity) }}
            </span>
            <span class="rounded-full bg-sky-100 px-2 py-0.5 text-xs font-bold text-aqua-700">
              {{ label("AlertState", alert.state) }}
            </span>
            <button
              ref="closeButton"
              type="button"
              class="ml-auto flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100"
              aria-label="Cerrar detalle"
              @click="close"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M6 6l12 12M18 6 6 18" />
              </svg>
            </button>
          </div>
          <h2 id="alert-detail-title" class="text-xl font-bold text-slate-900">
            {{ label("AlertType", alert.type) }}
            <span
              v-if="reading.value"
              :class="alert.severity === 'CRITICAL' ? 'text-rose-700' : 'text-amber-700'"
            >
              {{ reading.value }}
            </span>
          </h2>
          <p class="text-sm text-slate-600">
            <template v-if="reading.limit">Límite: {{ reading.limit }} bar · </template>
            hace {{ duration(alert.created_at) }}
          </p>
        </header>

        <div class="flex flex-1 flex-col gap-5 px-5 py-5 text-sm">
          <AlertNotificationsTimeline :alert="alert" :now="now" />

          <!-- #277: the readings close it; closing by hand is the exception -->
          <div v-if="alert.state !== 'RESOLVED'">
            <div v-if="confirming" class="flex flex-col gap-3 rounded-xl border border-slate-200 p-4">
              <p class="text-sm text-slate-700">
                ¿Cerrarla a mano? Se cierra sola tras 15 minutos de lecturas normales:
                hazlo solo si las lecturas no pueden confirmarlo (sensor cambiado o
                desactivado, falsa alarma).
              </p>
              <div class="grid grid-cols-2 gap-2">
                <button
                  ref="confirmButton"
                  type="button"
                  class="h-11 rounded-lg bg-aqua-600 px-4 text-sm font-bold text-white hover:bg-aqua-700 disabled:opacity-60"
                  :disabled="busy"
                  @click="$emit('resolve', alert.id)"
                >
                  {{ busy ? "Cerrando…" : "Sí, cerrarla" }}
                </button>
                <button
                  type="button"
                  class="h-11 rounded-lg border border-slate-300 bg-white px-4 text-sm font-semibold hover:bg-slate-50"
                  :disabled="busy"
                  @click="confirming = false"
                >
                  Cancelar
                </button>
              </div>
            </div>
            <button
              v-else
              type="button"
              class="text-sm font-medium text-aqua-700 underline-offset-2 hover:underline"
              @click="askConfirm"
            >
              Cerrar a mano…
            </button>
          </div>

          <section class="flex flex-col gap-1">
            <h3 class="text-xs font-bold uppercase tracking-wide text-slate-500">Dónde</h3>
            <p class="text-[15px] font-semibold text-slate-900">{{ alert.sensor_name }}</p>
            <p class="text-slate-600">
              {{ alert.organization_name }} · {{ alert.site_name }} · {{ floorLabel(alert.floor) }}
            </p>
          </section>

          <section class="flex flex-col gap-1">
            <h3 class="text-xs font-bold uppercase tracking-wide text-slate-500">
              {{ alert.state === "RESOLVED" ? "Cómo se cerró" : "Quién se ocupa" }}
            </h3>
            <p class="text-[15px] text-slate-900">
              {{ owner.main }}
              <span v-if="owner.sub" class="text-slate-500">· {{ owner.sub }}</span>
            </p>
          </section>

          <section aria-labelledby="alert-contact-title" class="flex flex-col gap-2">
            <h3 id="alert-contact-title" class="text-xs font-bold uppercase tracking-wide text-slate-500">
              Avisar al cliente
            </h3>
            <p v-if="contactStatus === 'loading'" class="text-slate-500">Cargando…</p>
            <p v-else-if="contactStatus === 'error'" class="text-slate-500">
              No se ha podido cargar el contacto.
            </p>
            <p v-else-if="!contact?.phone && !contact?.contact_email" class="text-slate-500">
              Sin teléfono ni email de contacto.
            </p>
            <template v-else>
              <div class="grid grid-cols-2 gap-2">
                <a
                  v-if="contact.phone"
                  :href="`tel:${contact.phone}`"
                  class="flex h-11 items-center justify-center gap-2 rounded-lg border border-slate-300 font-semibold text-slate-900 hover:border-aqua-400"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                    <path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2" />
                  </svg>
                  Llamar
                </a>
                <a
                  v-if="contact.contact_email"
                  :href="`mailto:${contact.contact_email}`"
                  class="flex h-11 items-center justify-center gap-2 rounded-lg border border-slate-300 font-semibold text-slate-900 hover:border-aqua-400"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                    <rect x="3" y="5" width="18" height="14" rx="2" />
                    <path d="m3 7 9 6 9-6" />
                  </svg>
                  Email
                </a>
              </div>
              <p class="break-all text-[13px] text-slate-500">
                {{ [contact.phone, contact.contact_email].filter(Boolean).join(" · ") }}
              </p>
            </template>
          </section>
        </div>

        <footer class="border-t border-slate-200 bg-slate-50 px-5 py-4">
          <p v-if="error" class="mb-3 rounded-lg bg-rose-50 p-3 text-sm text-rose-700" role="alert">
            {{ error }}
          </p>

          <router-link
            :to="sensorLink"
            class="flex h-11 items-center justify-center rounded-lg border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-900 hover:border-aqua-400"
          >
            Ver sensor
          </router-link>
        </footer>
      </aside>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, ref, watch } from "vue";
import AlertNotificationsTimeline from "./AlertNotificationsTimeline.vue";
import organizationsService from "../../services/organizations.service.js";
import { useLabels } from "../../composables/useLabels";
import { floorLabel } from "../../utils/floors";
import { alertReading, formatDuration, minutesSince } from "../../utils/alertText";

const props = defineProps({
  // The alert to show; null = closed
  alert: { type: Object, default: null },
  busy: { type: Boolean, default: false },
  error: { type: String, default: "" },
  // Changes on every refresh, so the notices timeline moves on (#275)
  now: { type: Date, default: () => new Date() },
});

const emit = defineEmits(["close", "resolve"]);

const { label, help } = useLabels();

const panel = ref(null);
const closeButton = ref(null);
const confirmButton = ref(null);
const confirming = ref(false);

const contact = ref(null);
const contactStatus = ref("idle");
// Contacts already asked for, so moving between alerts does not repeat requests
const contactCache = new Map();

const reading = computed(() => alertReading(props.alert));

const owner = computed(() => {
  const alert = props.alert;
  if (alert.state === "RESOLVED") {
    return {
      main: alert.resolved_by_name || "Por las lecturas",
      sub: `tardó ${formatDuration(alert.resolution_minutes)}`,
    };
  }
  if (alert.state === "ACTIVE") return { main: "Nadie todavía" };
  return {
    main: alert.acknowledged_by_name || "Alguien del cliente",
    sub: alert.acknowledged_at ? `desde hace ${duration(alert.acknowledged_at)}` : "",
  };
});

// The Sensores page opens this sensor in its side panel (#283)
const sensorLink = computed(() => ({
  name: "AdminSensors",
  query: { tab: "all", sensor: props.alert.sensor_id },
}));

function duration(value) {
  return formatDuration(minutesSince(value));
}

async function loadContact(organizationId) {
  if (contactCache.has(organizationId)) {
    contact.value = contactCache.get(organizationId);
    contactStatus.value = "success";
    return;
  }
  contactStatus.value = "loading";
  try {
    const response = await organizationsService.getOrganization(organizationId);
    contactCache.set(organizationId, response.data);
    if (props.alert?.organization_id !== organizationId) return;
    contact.value = response.data;
    contactStatus.value = "success";
  } catch {
    if (props.alert?.organization_id === organizationId) contactStatus.value = "error";
  }
}

// Element that had the focus before opening, to give it back on close
let opener = null;

watch(
  () => props.alert?.id,
  async (id, previous) => {
    confirming.value = false;
    if (!id) {
      opener?.focus?.();
      opener = null;
      return;
    }
    if (!previous) opener = document.activeElement;
    loadContact(props.alert.organization_id);
    await nextTick();
    closeButton.value?.focus();
  },
);

async function askConfirm() {
  confirming.value = true;
  await nextTick();
  confirmButton.value?.focus();
}

function close() {
  if (!props.busy) emit("close");
}

function trapFocus(event) {
  const focusable = panel.value?.querySelectorAll(
    'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
  );
  if (!focusable?.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}
</script>
