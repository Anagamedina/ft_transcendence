<!--
  NEW CLIENT WIZARD
  Four-step form to sign up a client: 1 Cliente, 2 Edificio, 3 Usuario, 4 Facturación.
  It only collects and validates the data; the parent creates the client and passes
  the result back in `created`, then the wizard shows the invitation link to send.
  Usage:
    <NewClientWizard :existing-names="names" :created="result" @submit="create" @cancel="close" @open="goToClient" />
-->

<template>
  <section class="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
    <!-- Success: the client exists, now the admin sends the invitation link -->
    <div v-if="created" class="space-y-4">
      <div class="flex items-center gap-3">
        <span class="flex h-9 w-9 items-center justify-center rounded-full bg-green-100 text-green-700" aria-hidden="true">✓</span>
        <h2 ref="heading" tabindex="-1" class="text-xl font-bold text-gray-900 focus:outline-none">
          {{ created.client.name }} creado
        </h2>
      </div>
      <p class="text-gray-700">
        Envía este enlace a {{ created.invitation.name }} ({{ created.invitation.email }}) para que active su cuenta.
      </p>
      <InviteLinkCopy :link="created.invitation.link" :expires-at="created.invitation.expires_at" />
      <div class="flex flex-wrap gap-3 border-t border-gray-200 pt-4">
        <button type="button" :class="BUTTON_PRIMARY" @click="$emit('open', created.client)">
          Ir a la ficha del cliente
        </button>
        <button type="button" :class="BUTTON_SECONDARY" @click="$emit('cancel')">Volver a la lista</button>
      </div>
    </div>

    <form v-else novalidate class="space-y-6" @submit.prevent="next">
      <div class="space-y-4">
        <h2 class="text-xl font-bold text-gray-900">Nuevo cliente</h2>

        <!-- Progress: one bar per step; aria-current marks the current one -->
        <ol aria-label="Pasos del alta" class="grid grid-cols-4 gap-2">
          <li
            v-for="(label, index) in STEPS"
            :key="label"
            class="flex flex-col gap-1.5 text-xs font-semibold sm:text-sm"
            :class="index <= step ? 'text-aqua-600' : 'text-gray-500'"
            :aria-current="index === step ? 'step' : undefined"
          >
            <span class="block h-1.5 rounded-full" :class="index <= step ? 'bg-aqua-600' : 'bg-gray-200'"></span>
            <span>
              {{ index + 1 }}. {{ label }}
              <span v-if="index < step" class="sr-only">(completado)</span>
            </span>
          </li>
        </ol>
      </div>

      <!-- Step title receives the focus when the step changes, so keyboard and
           screen reader users start reading the new step from the top -->
      <h3 ref="heading" tabindex="-1" class="text-lg font-semibold text-gray-800 focus:outline-none">
        Paso {{ step + 1 }} de {{ STEPS.length }}: {{ STEP_TITLES[step] }}
      </h3>

      <!-- 1. Cliente -->
      <div v-if="step === 0" class="grid gap-4 sm:grid-cols-2">
        <div class="flex flex-col gap-1 sm:col-span-2">
          <label :for="fieldId('name')" class="text-sm font-semibold text-gray-700">
            Nombre del cliente <span aria-hidden="true">*</span>
          </label>
          <input
            :id="fieldId('name')"
            :ref="(el) => (inputs.name = el)"
            v-model="form.client.name"
            type="text"
            required
            maxlength="120"
            autocomplete="organization"
            :class="inputClass('name')"
            :aria-invalid="Boolean(errors.name)"
            :aria-describedby="errors.name ? fieldId('name-error') : undefined"
          />
          <p v-if="errors.name" :id="fieldId('name-error')" class="text-sm text-red-700">{{ errors.name }}</p>
        </div>
        <div class="flex flex-col gap-1">
          <label :for="fieldId('contact_email')" class="text-sm font-semibold text-gray-700">Email de contacto</label>
          <input
            :id="fieldId('contact_email')"
            :ref="(el) => (inputs.contact_email = el)"
            v-model="form.client.contact_email"
            type="email"
            autocomplete="email"
            :class="inputClass('contact_email')"
            :aria-invalid="Boolean(errors.contact_email)"
            :aria-describedby="errors.contact_email ? fieldId('contact_email-error') : undefined"
          />
          <p v-if="errors.contact_email" :id="fieldId('contact_email-error')" class="text-sm text-red-700">
            {{ errors.contact_email }}
          </p>
        </div>
        <div class="flex flex-col gap-1">
          <label :for="fieldId('phone')" class="text-sm font-semibold text-gray-700">Teléfono</label>
          <input
            :id="fieldId('phone')"
            v-model="form.client.phone"
            type="tel"
            maxlength="30"
            autocomplete="tel"
            :class="inputClass('phone')"
          />
        </div>
        <p class="text-sm text-gray-600 sm:col-span-2">AquaGuard solo da servicio en Barcelona.</p>
      </div>

      <!-- 2. Edificio: the same form the sites view uses -->
      <SiteForm v-else-if="step === 1" ref="siteForm" v-model="form.site" />

      <!-- 3. Usuario: receives the invitation link -->
      <div v-else-if="step === 2" class="grid gap-4 sm:grid-cols-2">
        <p class="text-sm text-gray-600 sm:col-span-2">
          Al crear el cliente obtendrás un enlace de invitación para enviar a esta persona.
        </p>
        <div class="flex flex-col gap-1">
          <label :for="fieldId('user_name')" class="text-sm font-semibold text-gray-700">
            Nombre <span aria-hidden="true">*</span>
          </label>
          <input
            :id="fieldId('user_name')"
            :ref="(el) => (inputs.user_name = el)"
            v-model="form.user.name"
            type="text"
            required
            autocomplete="name"
            :class="inputClass('user_name')"
            :aria-invalid="Boolean(errors.user_name)"
            :aria-describedby="errors.user_name ? fieldId('user_name-error') : undefined"
          />
          <p v-if="errors.user_name" :id="fieldId('user_name-error')" class="text-sm text-red-700">
            {{ errors.user_name }}
          </p>
        </div>
        <div class="flex flex-col gap-1">
          <label :for="fieldId('user_email')" class="text-sm font-semibold text-gray-700">
            Email <span aria-hidden="true">*</span>
          </label>
          <input
            :id="fieldId('user_email')"
            :ref="(el) => (inputs.user_email = el)"
            v-model="form.user.email"
            type="email"
            required
            autocomplete="email"
            :class="inputClass('user_email')"
            :aria-invalid="Boolean(errors.user_email)"
            :aria-describedby="errors.user_email ? fieldId('user_email-error') : undefined"
          />
          <p v-if="errors.user_email" :id="fieldId('user_email-error')" class="text-sm text-red-700">
            {{ errors.user_email }}
          </p>
        </div>
      </div>

      <!-- 4. Facturación: optional, it can be completed later -->
      <div v-else class="grid gap-4 sm:grid-cols-2">
        <p class="text-sm text-gray-600 sm:col-span-2">Opcional: se puede completar más tarde.</p>
        <div class="flex flex-col gap-1">
          <label :for="fieldId('legal_name')" class="text-sm font-semibold text-gray-700">Razón social</label>
          <input
            :id="fieldId('legal_name')"
            v-model="form.client.legal_name"
            type="text"
            maxlength="200"
            :class="inputClass('legal_name')"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label :for="fieldId('tax_id')" class="text-sm font-semibold text-gray-700">NIF o CIF</label>
          <input
            :id="fieldId('tax_id')"
            v-model="form.client.tax_id"
            type="text"
            maxlength="30"
            :class="inputClass('tax_id')"
          />
        </div>
        <div class="flex flex-col gap-1 sm:col-span-2">
          <label :for="fieldId('billing_email')" class="text-sm font-semibold text-gray-700">Email de facturación</label>
          <input
            :id="fieldId('billing_email')"
            :ref="(el) => (inputs.billing_email = el)"
            v-model="form.client.billing_email"
            type="email"
            autocomplete="email"
            :class="inputClass('billing_email')"
            :aria-invalid="Boolean(errors.billing_email)"
            :aria-describedby="errors.billing_email ? fieldId('billing_email-error') : undefined"
          />
          <p v-if="errors.billing_email" :id="fieldId('billing_email-error')" class="text-sm text-red-700">
            {{ errors.billing_email }}
          </p>
        </div>
      </div>

      <div class="flex justify-between gap-3 border-t border-gray-200 pt-4">
        <button type="button" :class="BUTTON_SECONDARY" @click="back">
          {{ step === 0 ? 'Cancelar' : 'Atrás' }}
        </button>
        <!-- type="submit": Enter in any field also moves forward -->
        <button type="submit" :class="BUTTON_PRIMARY">
          {{ isLastStep ? 'Crear cliente' : 'Siguiente' }}
        </button>
      </div>
    </form>
  </section>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick, useId } from 'vue'
import SiteForm, { emptySite } from './SiteForm.vue'
import InviteLinkCopy from './InviteLinkCopy.vue'

const props = defineProps({
  // Names already in use: the API rejects a repeated name (case-insensitive)
  existingNames: { type: Array, default: () => [] },
  // Set by the parent after creating: { client, invitation: { name, email, link, expires_at } }
  created: { type: Object, default: null },
})

const emit = defineEmits(['submit', 'cancel', 'open'])

const STEPS = ['Cliente', 'Edificio', 'Usuario', 'Facturación']
const STEP_TITLES = ['datos del cliente', 'primer edificio', 'primer usuario', 'facturación']

const BUTTON_PRIMARY =
  'min-h-10 rounded-lg bg-aqua-600 px-4 text-sm font-semibold text-white hover:bg-aqua-700'
const BUTTON_SECONDARY =
  'min-h-10 rounded-lg border border-gray-300 bg-white px-4 text-sm font-semibold text-gray-700 hover:border-aqua-600'

// Same limit as OrganizationCreate.name (B1)
const NAME_MAX = 120

// Simple email check; the API does the full validation
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const step = ref(0)
const isLastStep = computed(() => step.value === STEPS.length - 1)

// Everything the wizard collects, grouped as the parent will send it
const form = reactive({
  client: { name: '', contact_email: '', phone: '', legal_name: '', tax_id: '', billing_email: '' },
  site: emptySite(),
  user: { name: '', email: '' },
})

const errors = reactive({})
const inputs = {}
const heading = ref(null)
const siteForm = ref(null)

const uid = useId()
function fieldId(name) {
  return `wizard-${uid}-${name}`
}

function inputClass(field) {
  const base =
    'w-full rounded-lg border bg-white px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-aqua-600'
  return errors[field] ? `${base} border-red-600` : `${base} border-gray-300`
}

function emailError(value, required) {
  const text = value.trim()
  if (text === '') return required ? 'Escribe el email.' : ''
  return EMAIL_PATTERN.test(text) ? '' : 'Escribe un email válido, por ejemplo nombre@empresa.com.'
}

// Rules of each step (the building step is validated by SiteForm itself).
// Each returns the error message of a field, or '' when the value is valid
const STEP_RULES = [
  {
    name: () => {
      const name = form.client.name.trim()
      if (name === '') return 'Escribe el nombre del cliente.'
      if (name.length > NAME_MAX) return `Máximo ${NAME_MAX} caracteres.`
      const taken = props.existingNames.some((existing) => existing.toLowerCase() === name.toLowerCase())
      return taken ? 'Ya hay un cliente con este nombre.' : ''
    },
    contact_email: () => emailError(form.client.contact_email, false),
  },
  {},
  {
    user_name: () => (form.user.name.trim() === '' ? 'Escribe el nombre de la persona.' : ''),
    user_email: () => emailError(form.user.email, true),
  },
  {
    billing_email: () => emailError(form.client.billing_email, false),
  },
]

// Validates the current step; focuses the first wrong field and returns false if any
function validateStep() {
  if (step.value === 1) return siteForm.value.validate()

  const rules = STEP_RULES[step.value]
  for (const field of Object.keys(rules)) errors[field] = rules[field]()
  const firstWrong = Object.keys(rules).find((field) => errors[field])
  if (firstWrong) {
    nextTick(() => inputs[firstWrong]?.focus())
    return false
  }
  return true
}

function next() {
  if (!validateStep()) return
  if (isLastStep.value) {
    emit('submit', {
      client: { ...form.client },
      site: { ...form.site },
      user: { name: form.user.name.trim(), email: form.user.email.trim() },
    })
  } else {
    step.value += 1
  }
}

function back() {
  if (step.value === 0) emit('cancel')
  else step.value -= 1
}

// A shown error disappears as soon as the user fixes the field
watch(
  form,
  () => {
    for (const rules of STEP_RULES) {
      for (const field of Object.keys(rules)) {
        if (errors[field]) errors[field] = rules[field]()
      }
    }
  },
  { deep: true }
)

// Move the focus to the title of the new step, or to the success message
watch([step, () => props.created], () => nextTick(() => heading.value?.focus()))
</script>
