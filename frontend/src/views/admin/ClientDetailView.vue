<!--
  ADMIN CLIENT DETAIL VIEW
  One client organization: header with status and counters, and five tabs
  (Edificios, Usuarios, Documentos, Datos, Acciones). Rendered inside AdminLayout.
  Data: organizations store (B1, B16) and sites store (B2).
  Usuarios: ClientUsersPanel (list, edit and remove users, B6, F23) and
  ClientInvitationsPanel (pending invitations and new invitation, B4).
  Documentos: ClientDocumentsPanel (documents of this client, B11).
-->

<script setup>
import { ref, computed, nextTick, watch } from "vue";
import { useRouter } from "vue-router";
import AdminLayout from "../../layouts/AdminLayout.vue";
import Tabs from "../../components/Tabs.vue";
import SitesSummary from "../../components/SitesSummary.vue";
import EmptyState from "../../components/EmptyState.vue";
import LoadingState from "../../components/LoadingState.vue";
import ErrorState from "../../components/ErrorState.vue";
import ClientActions from "../../components/ClientActions.vue";
import ClientUsersPanel from "../../components/ClientUsersPanel.vue";
import ClientInvitationsPanel from "../../components/ClientInvitationsPanel.vue";
import ClientDocumentsPanel from "../../components/ClientDocumentsPanel.vue";
import { useClientStatus } from "../../composables/useClientStatus";
import { useOrganizationsStore } from "../../stores/organizations";
import { useSitesStore } from "../../stores/sites";
import { useFormat } from "../../composables/useFormat";

const props = defineProps({
  // Comes from the route /admin/clients/:id (router option props: true)
  id: { type: String, required: true },
});

const router = useRouter();
const organizationsStore = useOrganizationsStore();
const sitesStore = useSitesStore();

// The store keeps the open client; every action replaces it with the API answer
const client = computed(() =>
  organizationsStore.current?.id === props.id
    ? organizationsStore.current
    : null,
);
const status = computed(() =>
  client.value ? useClientStatus(client.value) : null,
);
const clientSites = computed(() =>
  sitesStore.sites.filter((site) => site.organization_id === props.id),
);

// 404 is "client not found"; any other error offers a retry
const notFound = computed(
  () => organizationsStore.currentError?.code === "ORGANIZATION_NOT_FOUND",
);
const loading = computed(
  () => !client.value && organizationsStore.currentStatus === "loading",
);
const loadError = computed(
  () =>
    !client.value &&
    organizationsStore.currentStatus === "error" &&
    !notFound.value,
);

function loadClient() {
  organizationsStore.fetchOrganization(props.id).catch(() => {
    // The store keeps the error; the template shows it
  });
}

// Buildings of every client; this page keeps only the ones of this client
sitesStore.fetchSites().catch(() => {});

// Pill text: "En prueba · quedan 4 días" while the trial runs, only the label otherwise
const pillText = computed(() => {
  if (client.value.status !== "TRIAL" || status.value.trialEnded)
    return status.value.label;
  return `${status.value.label} · ${status.value.trialText.toLowerCase()}`;
});

// '21 oct 2026'
const { formatDate } = useFormat();

// ---------------------------------------------------------------------------
// Tabs: the Tabs component handles the keyboard and the ARIA attributes
// ---------------------------------------------------------------------------
const TABS = [
  { key: "sites", label: "Edificios" },
  { key: "users", label: "Usuarios" },
  { key: "documents", label: "Documentos" },
  { key: "data", label: "Datos" },
  { key: "actions", label: "Acciones" },
];

const activeTab = ref("sites");

// ---------------------------------------------------------------------------
// Datos tab: contact and billing fields, "—" when empty
// ---------------------------------------------------------------------------
const dataFields = computed(() => [
  { label: "Ciudad", value: client.value.city },
  { label: "Email de contacto", value: client.value.contact_email },
  { label: "Teléfono", value: client.value.phone },
  { label: "Razón social", value: client.value.legal_name },
  { label: "NIF o CIF", value: client.value.tax_id },
  { label: "Email de facturación", value: client.value.billing_email },
  { label: "Dirección fiscal", value: billingAddress.value },
  { label: "Plan", value: planText.value },
  { label: "Contratado", value: contractText.value },
  { label: "Cuenta (SEPA)", value: client.value.iban_masked },
  { label: "Cliente desde", value: formatDate(client.value.created_at) },
]);

// Saved by "Hazte cliente" (B14); empty for clients created by an admin
const PLAN_LABELS = {
  BASIC: "Básico",
  PRO: "Profesional",
  ENTERPRISE: "Empresa",
};
const PERIOD_LABELS = { MONTHLY: "mensual", YEARLY: "anual" };

const billingAddress = computed(() =>
  [client.value.billing_address, client.value.postal_code]
    .filter(Boolean)
    .join(", "),
);

const planText = computed(() => {
  const { plan, billing_period: period, subscribed_at: since } = client.value;
  if (!plan) return null;
  const parts = [PLAN_LABELS[plan] ?? plan, PERIOD_LABELS[period]]
    .filter(Boolean)
    .join(" ");
  return since ? `${parts}, desde el ${formatDate(since)}` : parts;
});

// "2 edificios y 12 sensores · 199 € / mes"
const contractText = computed(() => {
  const { contracted_sites: sitesCount, contracted_sensors: sensorsCount } =
    client.value;
  if (!sitesCount) return null;
  const count = (n, one, many) => `${n} ${n === 1 ? one : many}`;
  const price = client.value.monthly_price_eur;
  return [
    `${count(sitesCount, "edificio", "edificios")} y ${count(sensorsCount, "sensor", "sensores")}`,
    price != null ? `${price} € / mes` : null,
  ]
    .filter(Boolean)
    .join(" · ");
});

// ---------------------------------------------------------------------------
// Status actions: call the API and confirm the result in a status message
// ---------------------------------------------------------------------------
const feedback = ref("");
const feedbackIsError = ref(false);
const feedbackMessage = ref(null);
// True while an action is waiting for the API, so it is not sent twice
const busy = ref(false);

// Shows the result and moves the focus to it: the button that was clicked
// may disappear (e.g. "Suspender" becomes "Reactivar"), so the focus would be lost
function showFeedback(text, isError = false) {
  feedback.value = text;
  feedbackIsError.value = isError;
  nextTick(() => feedbackMessage.value?.focus());
}

// Runs one store action and shows its success text, built from the updated client,
// or the API error (e.g. 409 when another admin already changed the status)
async function runAction(action, successText) {
  if (busy.value) return;
  busy.value = true;
  try {
    const updated = await action(props.id);
    showFeedback(successText(updated));
  } catch (err) {
    showFeedback(
      err?.message ||
        "No se ha podido completar la acción. Inténtalo de nuevo.",
      true,
    );
  } finally {
    busy.value = false;
  }
}

function onExtend() {
  runAction(
    organizationsStore.extendTrial,
    (updated) =>
      `Prueba ampliada hasta el ${formatDate(updated.trial_ends_at)}.`,
  );
}

function onSuspend() {
  runAction(
    organizationsStore.suspend,
    (updated) => `${updated.name} está suspendido.`,
  );
}

function onReactivate() {
  runAction(
    organizationsStore.reactivate,
    (updated) => `${updated.name} se ha reactivado.`,
  );
}

// DELETE sends the exact name as confirmation (B16); the inline confirmation of
// ClientActions already asked the admin. Then back to the list
async function onDelete() {
  if (busy.value) return;
  busy.value = true;
  try {
    await organizationsStore.deleteOrganization(props.id, client.value.name);
    sitesStore.fetchSites().catch(() => {});
    router.push("/admin/clients");
  } catch (err) {
    showFeedback(
      err?.message ||
        "No se ha podido eliminar el cliente. Inténtalo de nuevo.",
      true,
    );
  } finally {
    busy.value = false;
  }
}

// A user was removed in the Usuarios tab: reload the client so its user_count
// (header counter and Acciones texts) comes from the API again
function onUserRemoved() {
  organizationsStore.fetchOrganization(props.id).catch(() => {});
}

// Load on open (declared last: it uses the refs above) and when the route changes to another client
watch(
  () => props.id,
  () => {
    feedback.value = "";
    loadClient();
  },
  { immediate: true },
);
</script>

<template>
  <AdminLayout>
    <div class="space-y-6">
      <router-link
        to="/admin/clients"
        class="text-sm text-aqua-700 hover:underline"
      >
        ← Volver a clientes
      </router-link>

      <LoadingState v-if="loading" message="Cargando cliente…" />

      <ErrorState
        v-else-if="loadError"
        :message="organizationsStore.currentError?.message"
        @retry="loadClient"
      />

      <EmptyState
        v-else-if="!client"
        title="Cliente no encontrado"
        message="Puede que se haya eliminado o que el enlace no sea correcto."
        icon="building"
      />

      <template v-else>
        <!-- Header: name, status, contact line and counters -->
        <header
          class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"
        >
          <div class="space-y-1">
            <div class="flex flex-wrap items-center gap-3">
              <h1 class="text-2xl font-bold text-slate-900">
                {{ client.name }}
              </h1>
              <span
                class="inline-block whitespace-nowrap rounded-full px-3 py-1 text-xs font-semibold"
                :class="status.pillClass"
              >
                {{ pillText }}
              </span>
            </div>
            <p class="text-sm text-slate-600">
              Cliente desde {{ formatDate(client.created_at) }}
              <template v-if="client.contact_email">
                · {{ client.contact_email }}</template
              >
            </p>
          </div>

          <dl class="grid grid-cols-4 gap-2 text-center">
            <div class="rounded-lg border border-slate-200 bg-white px-3 py-2">
              <dt class="text-xs text-slate-600">Edificios</dt>
              <dd class="text-xl font-bold tabular-nums text-slate-900">
                {{ client.site_count }}
              </dd>
            </div>
            <div class="rounded-lg border border-slate-200 bg-white px-3 py-2">
              <dt class="text-xs text-slate-600">Sensores</dt>
              <dd class="text-xl font-bold tabular-nums text-slate-900">
                {{ client.sensor_count }}
              </dd>
            </div>
            <div class="rounded-lg border border-slate-200 bg-white px-3 py-2">
              <dt class="text-xs text-slate-600">Usuarios</dt>
              <dd class="text-xl font-bold tabular-nums text-slate-900">
                {{ client.user_count }}
              </dd>
            </div>
            <div class="rounded-lg border border-slate-200 bg-white px-3 py-2">
              <dt class="text-xs text-slate-600">Alertas</dt>
              <dd
                class="text-xl font-bold tabular-nums"
                :class="
                  client.critical_alerts > 0 ? 'text-danger-dark' : 'text-slate-900'
                "
              >
                {{ client.open_alerts }}
              </dd>
            </div>
          </dl>
        </header>

        <!-- Result of the last action; role="status" announces it to screen readers -->
        <p
          ref="feedbackMessage"
          role="status"
          tabindex="-1"
          class="text-sm font-semibold"
          :class="[
            feedbackIsError ? 'text-danger-dark' : 'text-success-dark',
            feedback
              ? `rounded-lg border px-4 py-2 focus:outline-none focus:ring-2 focus:ring-aqua-600 ${
                  feedbackIsError
                    ? 'border-danger/40 bg-danger-light'
                    : 'border-success/40 bg-success-light'
                }`
              : '',
          ]"
        >
          {{ feedback }}
        </p>

        <Tabs v-model="activeTab" :tabs="TABS" label="Secciones del cliente">
          <!-- Edificios -->
          <template #sites>
            <SitesSummary :sites="clientSites" />
          </template>

          <!-- Usuarios -->
          <template #users>
            <div class="space-y-4">
              <ClientUsersPanel
                :organization-id="client.id"
                @removed="onUserRemoved"
              />

              <ClientInvitationsPanel :organization-id="client.id" />
            </div>
          </template>

          <!-- Documentos: documents of this client (B11) -->
          <template #documents>
            <ClientDocumentsPanel
              :organization-id="client.id"
              :sites="clientSites"
            />
          </template>

          <!-- Datos -->
          <template #data>
            <div class="rounded-xl border border-slate-200 bg-white p-5">
              <dl class="grid gap-x-8 gap-y-4 sm:grid-cols-2">
                <div v-for="field in dataFields" :key="field.label">
                  <dt class="text-sm text-slate-600">{{ field.label }}</dt>
                  <dd class="font-semibold text-slate-900 break-words">
                    {{ field.value || "—" }}
                  </dd>
                </div>
              </dl>
            </div>
          </template>

          <!-- Acciones -->
          <template #actions>
            <ClientActions
              :client="client"
              @extend="onExtend"
              @suspend="onSuspend"
              @reactivate="onReactivate"
              @delete="onDelete"
            />
          </template>
        </Tabs>
      </template>
    </div>
  </AdminLayout>
</template>
