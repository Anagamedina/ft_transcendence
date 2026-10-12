<!--
  ADMIN CLIENT DETAIL VIEW
  One client organization: header with status and counters, and five tabs
  (Edificios, Usuarios, Documentos, Datos, Acciones). Rendered inside AdminLayout.
  Uses temporary mock data until the organizations, sites and users stores exist (data area).
-->

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '../../layouts/AdminLayout.vue'
import SitesSummary from '../../components/SitesSummary.vue'
import EmptyState from '../../components/EmptyState.vue'
import ClientActions from '../../components/ClientActions.vue'
import InviteLinkCopy from '../../components/InviteLinkCopy.vue'
import { useClientStatus } from '../../composables/useClientStatus'
// TODO: replace these mocks with store data and actions (data area) and delete this import
import {
  findClient,
  sitesOf,
  usersOf,
  invitationsOf,
  suspendClient,
  reactivateClient,
  extendTrial,
  activateClient,
  deleteClient,
  inviteUser,
} from './mockClients'

const props = defineProps({
  // Comes from the route /admin/clients/:id (router option props: true)
  id: { type: String, required: true },
})

const router = useRouter()

// The mock clients are reactive, so the page updates after each action
const client = computed(() => findClient(props.id))
const status = computed(() => (client.value ? useClientStatus(client.value) : null))
const clientSites = computed(() => sitesOf(props.id))
const clientUsers = computed(() => usersOf(props.id))
const pendingInvitations = computed(() => invitationsOf(props.id))

// Pill text: "En prueba · quedan 4 días" while the trial runs, only the label otherwise
const pillText = computed(() => {
  if (client.value.status !== 'TRIAL' || status.value.trialEnded) return status.value.label
  return `${status.value.label} · ${status.value.trialText.toLowerCase()}`
})

const longDate = new Intl.DateTimeFormat('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })
function formatDate(isoDate) {
  return longDate.format(new Date(isoDate))
}

// ---------------------------------------------------------------------------
// Tabs (WAI-ARIA tabs pattern: arrow keys move between tabs)
// ---------------------------------------------------------------------------
const TABS = [
  { key: 'sites', label: 'Edificios' },
  { key: 'users', label: 'Usuarios' },
  { key: 'documents', label: 'Documentos' },
  { key: 'data', label: 'Datos' },
  { key: 'actions', label: 'Acciones' },
]

const activeTab = ref('sites')
const tabButtons = ref([])

function selectTab(index) {
  activeTab.value = TABS[index].key
  nextTick(() => tabButtons.value[index]?.focus())
}

// Left/Right go to the previous/next tab (wrapping around), Home/End to the first/last
function onTabKeydown(event, index) {
  const last = TABS.length - 1
  const moves = {
    ArrowRight: index === last ? 0 : index + 1,
    ArrowLeft: index === 0 ? last : index - 1,
    Home: 0,
    End: last,
  }
  if (!(event.key in moves)) return
  event.preventDefault()
  selectTab(moves[event.key])
}

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
// Status actions: run the action and confirm the result in a status message
// ---------------------------------------------------------------------------
const feedback = ref('')

function onExtend() {
  extendTrial(client.value)
  feedback.value = `Prueba ampliada hasta el ${formatDate(client.value.trial_ends_at)}.`
}

function onActivate() {
  activateClient(client.value)
  feedback.value = `${client.value.name} ya es cliente activo.`
}

function onSuspend() {
  suspendClient(client.value)
  feedback.value = `${client.value.name} está suspendido.`
}

function onReactivate() {
  reactivateClient(client.value)
  feedback.value = `${client.value.name} se ha reactivado.`
}

function onDelete() {
  deleteClient(client.value)
  router.push('/admin/clients')
}

// ---------------------------------------------------------------------------
// Usuarios tab: invite a new user and show the link to send
// ---------------------------------------------------------------------------
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const invite = ref({ name: '', email: '' })
const inviteError = ref('')
const lastInvitation = ref(null)
const inviteEmailInput = ref(null)

function onInvite() {
  const email = invite.value.email.trim()
  const name = invite.value.name.trim()
  if (!EMAIL_PATTERN.test(email)) {
    inviteError.value = 'Escribe un email válido, por ejemplo nombre@empresa.com.'
    inviteEmailInput.value?.focus()
    return
  }
  inviteError.value = ''
  lastInvitation.value = inviteUser(client.value, { name: name || email, email })
  invite.value = { name: '', email: '' }
}

const INPUT_CLASS =
  'w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-aqua-600'
</script>

<template>
  <AdminLayout>
    <div class="space-y-6">
      <router-link to="/admin/clients" class="text-sm text-aqua-700 hover:underline">
        ← Volver a clientes
      </router-link>

      <EmptyState
        v-if="!client"
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
          role="status"
          class="text-sm font-semibold text-green-800"
          :class="feedback ? 'rounded-lg border border-green-200 bg-green-50 px-4 py-2' : ''"
        >
          {{ feedback }}
        </p>

        <!-- Tabs: only the active one is in the Tab order; arrows move between them -->
        <div class="overflow-x-auto">
          <div role="tablist" aria-label="Secciones del cliente" class="flex min-w-max gap-1 border-b-2 border-gray-200">
            <button
              v-for="(tab, index) in TABS"
              :id="`tab-${tab.key}`"
              :key="tab.key"
              :ref="(el) => (tabButtons[index] = el)"
              type="button"
              role="tab"
              :aria-selected="activeTab === tab.key"
              :aria-controls="`panel-${tab.key}`"
              :tabindex="activeTab === tab.key ? 0 : -1"
              class="-mb-0.5 border-b-2 px-4 py-2.5 text-base"
              :class="
                activeTab === tab.key
                  ? 'border-aqua-600 font-bold text-aqua-600'
                  : 'border-transparent text-gray-600 hover:text-aqua-600'
              "
              @click="selectTab(index)"
              @keydown="onTabKeydown($event, index)"
            >
              {{ tab.label }}
            </button>
          </div>
        </div>

        <!-- Edificios -->
        <div
          v-if="activeTab === 'sites'"
          id="panel-sites"
          role="tabpanel"
          aria-labelledby="tab-sites"
          tabindex="0"
        >
          <SitesSummary :sites="clientSites" />
        </div>

        <!-- Usuarios -->
        <div
          v-else-if="activeTab === 'users'"
          id="panel-users"
          role="tabpanel"
          aria-labelledby="tab-users"
          tabindex="0"
          class="space-y-4"
        >
          <EmptyState
            v-if="clientUsers.length === 0"
            title="Este cliente aún no tiene usuarios"
            message="Invita a alguien de su equipo con el formulario de abajo."
            icon="users"
            compact
          />
          <div v-else class="overflow-x-auto rounded-xl border border-gray-200 bg-white">
            <table class="w-full min-w-[520px] text-sm">
              <caption class="sr-only">Usuarios de {{ client.name }}</caption>
              <thead class="bg-gray-50 text-left text-gray-600">
                <tr>
                  <th scope="col" class="px-4 py-3 font-semibold">Nombre</th>
                  <th scope="col" class="px-4 py-3 font-semibold">Email</th>
                  <th scope="col" class="px-4 py-3 font-semibold">Alta</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in clientUsers" :key="user.id" class="border-t border-gray-200">
                  <th scope="row" class="px-4 py-3 text-left font-semibold text-gray-800">{{ user.name }}</th>
                  <td class="px-4 py-3 text-gray-700">{{ user.email }}</td>
                  <td class="whitespace-nowrap px-4 py-3 text-gray-600">{{ formatDate(user.created_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>

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
            <form novalidate class="grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end" @submit.prevent="onInvite">
              <div class="flex flex-col gap-1">
                <label for="invite-name" class="text-sm font-semibold text-gray-700">Nombre</label>
                <input id="invite-name" v-model="invite.name" type="text" autocomplete="name" :class="INPUT_CLASS" />
              </div>
              <div class="flex flex-col gap-1">
                <label for="invite-email" class="text-sm font-semibold text-gray-700">
                  Email <span aria-hidden="true">*</span>
                </label>
                <input
                  id="invite-email"
                  ref="inviteEmailInput"
                  v-model="invite.email"
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
                class="min-h-10 rounded-lg bg-aqua-600 px-4 text-sm font-semibold text-white hover:bg-aqua-700"
              >
                Crear invitación
              </button>
              <p v-if="inviteError" id="invite-email-error" class="text-sm text-red-700 sm:col-span-3">
                {{ inviteError }}
              </p>
            </form>

            <div v-if="lastInvitation" class="space-y-2 border-t border-gray-200 pt-4">
              <p class="text-sm text-gray-700">Envía este enlace a {{ lastInvitation.email }} para que active su cuenta.</p>
              <InviteLinkCopy :link="lastInvitation.link" :expires-at="lastInvitation.expires_at" />
            </div>
          </section>
        </div>

        <!-- Documentos: arrives with the documents API (B11) and its components (F14) -->
        <div
          v-else-if="activeTab === 'documents'"
          id="panel-documents"
          role="tabpanel"
          aria-labelledby="tab-documents"
          tabindex="0"
        >
          <EmptyState
            title="Todavía no hay documentos"
            message="Aquí aparecerán los planos, informes y facturas de sus edificios."
            icon="building"
          />
        </div>

        <!-- Datos -->
        <div
          v-else-if="activeTab === 'data'"
          id="panel-data"
          role="tabpanel"
          aria-labelledby="tab-data"
          tabindex="0"
          class="rounded-xl border border-gray-200 bg-white p-5"
        >
          <dl class="grid gap-x-8 gap-y-4 sm:grid-cols-2">
            <div v-for="field in dataFields" :key="field.label">
              <dt class="text-sm text-gray-600">{{ field.label }}</dt>
              <dd class="font-semibold text-gray-900 break-words">{{ field.value || '—' }}</dd>
            </div>
          </dl>
        </div>

        <!-- Acciones -->
        <div
          v-else
          id="panel-actions"
          role="tabpanel"
          aria-labelledby="tab-actions"
          tabindex="0"
        >
          <ClientActions
            :client="client"
            @extend="onExtend"
            @activate="onActivate"
            @suspend="onSuspend"
            @reactivate="onReactivate"
            @delete="onDelete"
          />
        </div>
      </template>
    </div>
  </AdminLayout>
</template>
