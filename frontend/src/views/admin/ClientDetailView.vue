<!--
  ADMIN CLIENT DETAIL VIEW
  One client organization: header with status and counters, and five tabs
  (Edificios, Usuarios, Documentos, Datos, Acciones). Rendered inside AdminLayout.
  Data: organizations store (B1, B16; invitations B4 still mocked inside its service)
  and sites store (B2). There is no users list in the API yet, so Usuarios shows the count.
-->

<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '../../layouts/AdminLayout.vue'
import Tabs from '../../components/Tabs.vue'
import SitesSummary from '../../components/SitesSummary.vue'
import EmptyState from '../../components/EmptyState.vue'
import LoadingState from '../../components/LoadingState.vue'
import ErrorState from '../../components/ErrorState.vue'
import ClientActions from '../../components/ClientActions.vue'
import InviteLinkCopy from '../../components/InviteLinkCopy.vue'
import { useClientStatus } from '../../composables/useClientStatus'
import { useOrganizationsStore } from '../../stores/organizations'
import { useSitesStore } from '../../stores/sites'
import { useFormat } from '../../composables/useFormat'

const props = defineProps({
  // Comes from the route /admin/clients/:id (router option props: true)
  id: { type: String, required: true },
})

const router = useRouter()
const organizationsStore = useOrganizationsStore()
const sitesStore = useSitesStore()

// The store keeps the open client; every action replaces it with the API answer
const client = computed(() =>
  organizationsStore.current?.id === props.id ? organizationsStore.current : null
)
const status = computed(() => (client.value ? useClientStatus(client.value) : null))
const clientSites = computed(() => sitesStore.sites.filter((site) => site.organization_id === props.id))
const pendingInvitations = computed(() => organizationsStore.invitations)

// 404 is "client not found"; any other error offers a retry
const notFound = computed(() => organizationsStore.currentError?.code === 'ORGANIZATION_NOT_FOUND')
const loading = computed(() => !client.value && organizationsStore.currentStatus === 'loading')
const loadError = computed(() => !client.value && organizationsStore.currentStatus === 'error' && !notFound.value)

function loadClient() {
  organizationsStore.fetchOrganization(props.id).catch(() => {
    // The store keeps the error; the template shows it
  })
  organizationsStore.fetchInvitations(props.id)
}

// Buildings of every client; this page keeps only the ones of this client
sitesStore.fetchSites().catch(() => {})

// Pill text: "En prueba · quedan 4 días" while the trial runs, only the label otherwise
const pillText = computed(() => {
  if (client.value.status !== 'TRIAL' || status.value.trialEnded) return status.value.label
  return `${status.value.label} · ${status.value.trialText.toLowerCase()}`
})

// '21 oct 2026'
const { formatDate } = useFormat()

// ---------------------------------------------------------------------------
// Tabs: the Tabs component handles the keyboard and the ARIA attributes
// ---------------------------------------------------------------------------
const TABS = [
  { key: 'sites', label: 'Edificios' },
  { key: 'users', label: 'Usuarios' },
  { key: 'documents', label: 'Documentos' },
  { key: 'data', label: 'Datos' },
  { key: 'actions', label: 'Acciones' },
]

const activeTab = ref('sites')

// ---------------------------------------------------------------------------
// Datos tab: contact and billing fields, "—" when empty
// ---------------------------------------------------------------------------
const dataFields = computed(() => [
  { label: 'Ciudad', value: client.value.city },
  { label: 'Email de contacto', value: client.value.contact_email },
  { label: 'Teléfono', value: client.value.phone },
  { label: 'Razón social', value: client.value.legal_name },
  { label: 'NIF o CIF', value: client.value.tax_id },
  { label: 'Email de facturación', value: client.value.billing_email },
  { label: 'Cliente desde', value: formatDate(client.value.created_at) },
])

// ---------------------------------------------------------------------------
// Status actions: call the API and confirm the result in a status message
// ---------------------------------------------------------------------------
const feedback = ref('')
const feedbackIsError = ref(false)
const feedbackMessage = ref(null)
// True while an action is waiting for the API, so it is not sent twice
const busy = ref(false)

// Shows the result and moves the focus to it: the button that was clicked
// may disappear (e.g. "Suspender" becomes "Reactivar"), so the focus would be lost
function showFeedback(text, isError = false) {
  feedback.value = text
  feedbackIsError.value = isError
  nextTick(() => feedbackMessage.value?.focus())
}

// Runs one store action and shows its success text, built from the updated client,
// or the API error (e.g. 409 when another admin already changed the status)
async function runAction(action, successText) {
  if (busy.value) return
  busy.value = true
  try {
    const updated = await action(props.id)
    showFeedback(successText(updated))
  } catch (err) {
    showFeedback(err?.message || 'No se ha podido completar la acción. Inténtalo de nuevo.', true)
  } finally {
    busy.value = false
  }
}

function onExtend() {
  runAction(organizationsStore.extendTrial, (updated) => `Prueba ampliada hasta el ${formatDate(updated.trial_ends_at)}.`)
}

function onActivate() {
  runAction(organizationsStore.activate, (updated) => `${updated.name} ya es cliente activo.`)
}

function onSuspend() {
  runAction(organizationsStore.suspend, (updated) => `${updated.name} está suspendido.`)
}

function onReactivate() {
  runAction(organizationsStore.reactivate, (updated) => `${updated.name} se ha reactivado.`)
}

// DELETE sends the exact name as confirmation (B16); the inline confirmation of
// ClientActions already asked the admin. Then back to the list
async function onDelete() {
  if (busy.value) return
  busy.value = true
  try {
    await organizationsStore.deleteOrganization(props.id, client.value.name)
    sitesStore.fetchSites().catch(() => {})
    router.push('/admin/clients')
  } catch (err) {
    showFeedback(err?.message || 'No se ha podido eliminar el cliente. Inténtalo de nuevo.', true)
  } finally {
    busy.value = false
  }
}

// Users of the client: the API only returns how many there are
const usersText = computed(() => {
  const count = client.value.user_count
  return count === 1 ? '1 persona tiene acceso a AquaGuard.' : `${count} personas tienen acceso a AquaGuard.`
})

// ---------------------------------------------------------------------------
// Usuarios tab: invite a new user and show the link to send
// ---------------------------------------------------------------------------
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

// The invitation only carries the email (B4): the person writes their name when accepting
const inviteEmail = ref('')
const inviteError = ref('')
const inviting = ref(false)
// InvitationSentResponse: the only answer with the link (url)
const lastInvitation = ref(null)
const inviteEmailInput = ref(null)

async function onInvite() {
  const email = inviteEmail.value.trim()
  if (!EMAIL_PATTERN.test(email)) {
    inviteError.value = 'Escribe un email válido, por ejemplo nombre@empresa.com.'
    inviteEmailInput.value?.focus()
    return
  }
  inviteError.value = ''
  inviting.value = true
  try {
    lastInvitation.value = await organizationsStore.createInvitation({ email, organization_id: props.id })
    inviteEmail.value = ''
  } catch (err) {
    inviteError.value = err?.message || 'No se ha podido crear la invitación. Inténtalo de nuevo.'
    inviteEmailInput.value?.focus()
  } finally {
    inviting.value = false
  }
}

// Load on open (declared last: it uses the refs above) and when the route changes to another client
watch(
  () => props.id,
  () => {
    feedback.value = ''
    lastInvitation.value = null
    loadClient()
  },
  { immediate: true }
)

const INPUT_CLASS =
  'w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-aqua-600'
</script>

<template>
  <AdminLayout>
    <div class="space-y-6">
      <router-link to="/admin/clients" class="text-sm text-aqua-700 hover:underline">
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
        <header class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div class="space-y-1">
            <div class="flex flex-wrap items-center gap-3">
              <h1 class="text-2xl font-bold text-gray-900">{{ client.name }}</h1>
              <span
                class="inline-block whitespace-nowrap rounded-full px-3 py-1 text-xs font-semibold"
                :class="status.pillClass"
              >
                {{ pillText }}
              </span>
            </div>
            <p class="text-sm text-gray-600">
              Cliente desde {{ formatDate(client.created_at) }}
              <template v-if="client.contact_email"> · {{ client.contact_email }}</template>
            </p>
          </div>

          <dl class="grid grid-cols-4 gap-2 text-center">
            <div class="rounded-lg border border-gray-200 bg-white px-3 py-2">
              <dt class="text-xs text-gray-600">Edificios</dt>
              <dd class="text-xl font-bold tabular-nums text-gray-900">{{ client.site_count }}</dd>
            </div>
            <div class="rounded-lg border border-gray-200 bg-white px-3 py-2">
              <dt class="text-xs text-gray-600">Sensores</dt>
              <dd class="text-xl font-bold tabular-nums text-gray-900">{{ client.sensor_count }}</dd>
            </div>
            <div class="rounded-lg border border-gray-200 bg-white px-3 py-2">
              <dt class="text-xs text-gray-600">Usuarios</dt>
              <dd class="text-xl font-bold tabular-nums text-gray-900">{{ client.user_count }}</dd>
            </div>
            <div class="rounded-lg border border-gray-200 bg-white px-3 py-2">
              <dt class="text-xs text-gray-600">Alertas</dt>
              <dd
                class="text-xl font-bold tabular-nums"
                :class="client.critical_alerts > 0 ? 'text-red-700' : 'text-gray-900'"
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
            feedbackIsError ? 'text-red-800' : 'text-green-800',
            feedback
              ? `rounded-lg border px-4 py-2 focus:outline-none focus:ring-2 focus:ring-aqua-600 ${
                  feedbackIsError ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'
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
              <EmptyState
                v-if="client.user_count === 0"
                title="Este cliente aún no tiene usuarios"
                message="Invita a alguien de su equipo con el formulario de abajo."
                icon="users"
                compact
              />
              <p v-else class="rounded-xl border border-gray-200 bg-white p-5 text-gray-800">{{ usersText }}</p>

              <section
                v-if="pendingInvitations.length > 0"
                class="space-y-2 rounded-xl border border-gray-200 bg-white p-5"
                aria-labelledby="pending-title"
              >
                <h2 id="pending-title" class="font-bold text-gray-900">Invitaciones pendientes</h2>
                <ul class="space-y-1 text-sm text-gray-700">
                  <li v-for="invitation in pendingInvitations" :key="invitation.id">
                    {{ invitation.email }} · caduca el {{ formatDate(invitation.expires_at) }}
                  </li>
                </ul>
              </section>

              <!-- Invite form: creates an invitation (B4) and shows the link to send -->
              <section class="space-y-4 rounded-xl border border-gray-200 bg-white p-5" aria-labelledby="invite-title">
                <h2 id="invite-title" class="font-bold text-gray-900">Invitar usuario</h2>
                <form novalidate class="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end" @submit.prevent="onInvite">
                  <div class="flex flex-col gap-1">
                    <label for="invite-email" class="text-sm font-semibold text-gray-700">
                      Email <span aria-hidden="true">*</span>
                    </label>
                    <input
                      id="invite-email"
                      ref="inviteEmailInput"
                      v-model="inviteEmail"
                      type="email"
                      required
                      autocomplete="email"
                      :class="INPUT_CLASS"
                      :aria-invalid="Boolean(inviteError)"
                      :aria-describedby="inviteError ? 'invite-email-error' : undefined"
                    />
                  </div>
                  <button
                    type="submit"
                    class="min-h-10 rounded-lg bg-aqua-600 px-4 text-sm font-semibold text-white hover:bg-aqua-700 disabled:cursor-wait disabled:opacity-60"
                    :disabled="inviting"
                    :aria-busy="inviting"
                  >
                    {{ inviting ? 'Creando…' : 'Crear invitación' }}
                  </button>
                  <p v-if="inviteError" id="invite-email-error" class="text-sm text-red-700 sm:col-span-2">
                    {{ inviteError }}
                  </p>
                </form>

                <div v-if="lastInvitation" class="space-y-2 border-t border-gray-200 pt-4">
                  <p class="text-sm text-gray-700">Envía este enlace a {{ lastInvitation.email }} para que active su cuenta.</p>
                  <InviteLinkCopy :link="lastInvitation.url" :expires-at="lastInvitation.expires_at" />
                </div>
              </section>
            </div>
          </template>

          <!-- Documentos: arrives with the documents API (B11) and its components (F14) -->
          <template #documents>
            <EmptyState
              title="Todavía no hay documentos"
              message="Aquí aparecerán los planos, informes y facturas de sus edificios."
              icon="building"
            />
          </template>

          <!-- Datos -->
          <template #data>
            <div class="rounded-xl border border-gray-200 bg-white p-5">
              <dl class="grid gap-x-8 gap-y-4 sm:grid-cols-2">
                <div v-for="field in dataFields" :key="field.label">
                  <dt class="text-sm text-gray-600">{{ field.label }}</dt>
                  <dd class="font-semibold text-gray-900 break-words">{{ field.value || '—' }}</dd>
                </div>
              </dl>
            </div>
          </template>

          <!-- Acciones -->
          <template #actions>
            <ClientActions
              :client="client"
              @extend="onExtend"
              @activate="onActivate"
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