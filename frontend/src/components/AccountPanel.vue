<template>
  <div class="mx-auto max-w-3xl space-y-6">
    <header>
      <h1 class="text-3xl font-bold text-gray-900">Mi cuenta</h1>
      <p class="mt-2 text-sm text-gray-600">Gestiona tus datos y contraseña.</p>
    </header>

    <section class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 class="mb-4 text-lg font-bold text-gray-800">Datos personales</h2>
      <form class="space-y-4" @submit.prevent="saveProfile">
        <label class="block text-sm font-medium text-gray-700">
          Nombre
          <input v-model="name" required maxlength="120" class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
        </label>
        <label class="block text-sm font-medium text-gray-700">
          Email
          <input :value="authStore.user?.email" disabled class="mt-1 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-gray-500" />
        </label>
        <p v-if="profileError" class="text-sm text-red-700" role="alert">{{ profileError }}</p>
        <p v-if="profileSaved" class="text-sm text-green-700" role="status">Datos actualizados.</p>
        <button type="submit" :disabled="profileLoading" class="rounded-lg bg-aqua-600 px-4 py-2 font-semibold text-white disabled:opacity-50">
          {{ profileLoading ? 'Guardando…' : 'Guardar cambios' }}
        </button>
      </form>
    </section>

    <section class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 class="mb-4 text-lg font-bold text-gray-800">Cambiar contraseña</h2>
      <form class="space-y-4" @submit.prevent="savePassword">
        <label v-for="field in passwordFields" :key="field.key" class="block text-sm font-medium text-gray-700">
          {{ field.label }}
          <input v-model="password[field.key]" type="password" :required="true" :maxlength="128" class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
        </label>
        <p v-if="passwordError" class="text-sm text-red-700" role="alert">{{ passwordError }}</p>
        <p v-if="passwordSaved" class="text-sm text-green-700" role="status">Contraseña actualizada.</p>
        <button type="submit" :disabled="passwordLoading" class="rounded-lg bg-aqua-600 px-4 py-2 font-semibold text-white disabled:opacity-50">
          {{ passwordLoading ? 'Actualizando…' : 'Cambiar contraseña' }}
        </button>
      </form>
    </section>

    <section v-if="authStore.organization" class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 class="mb-4 text-lg font-bold text-gray-800">Organización y suscripción</h2>
      <dl class="grid gap-3 sm:grid-cols-2">
        <div><dt class="text-sm text-gray-500">Organización</dt><dd class="font-medium">{{ authStore.organization.name }}</dd></div>
        <div><dt class="text-sm text-gray-500">Estado</dt><dd class="font-medium">{{ authStore.organization.status }}</dd></div>
        <div v-if="authStore.organization.trial_ends_at"><dt class="text-sm text-gray-500">Fin de prueba</dt><dd class="font-medium">{{ formatDate(authStore.organization.trial_ends_at) }}</dd></div>
        <div v-if="authStore.termsVersion"><dt class="text-sm text-gray-500">Versión de términos</dt><dd class="font-medium">{{ authStore.termsVersion }}</dd></div>
      </dl>
    </section>

    <p v-if="authStore.lastLoginAt" class="text-sm text-gray-500">Último acceso: {{ formatDate(authStore.lastLoginAt) }}</p>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const name = ref(authStore.user?.name ?? '')
const profileLoading = ref(false)
const profileError = ref('')
const profileSaved = ref(false)
const passwordLoading = ref(false)
const passwordError = ref('')
const passwordSaved = ref(false)
const password = ref({ current_password: '', new_password: '', confirmation: '' })
const passwordFields = [
  { key: 'current_password', label: 'Contraseña actual' },
  { key: 'new_password', label: 'Nueva contraseña' },
  { key: 'confirmation', label: 'Repite la nueva contraseña' },
]

watch(() => authStore.user?.name, (value) => { if (value) name.value = value })

async function saveProfile() {
  profileLoading.value = true
  profileError.value = ''
  profileSaved.value = false
  try {
    await authStore.updateMe({ name: name.value })
    profileSaved.value = true
  } catch (error) {
    profileError.value = error.message || 'No se han podido guardar los datos.'
  } finally {
    profileLoading.value = false
  }
}

async function savePassword() {
  passwordLoading.value = true
  passwordError.value = ''
  passwordSaved.value = false
  if (password.value.new_password !== password.value.confirmation) {
    passwordError.value = 'Las contraseñas nuevas no coinciden.'
    passwordLoading.value = false
    return
  }
  try {
    await authStore.changePassword({
      current_password: password.value.current_password,
      new_password: password.value.new_password,
    })
    password.value = { current_password: '', new_password: '', confirmation: '' }
    passwordSaved.value = true
  } catch (error) {
    passwordError.value = error.code === 'WRONG_PASSWORD'
      ? 'La contraseña actual no es correcta.'
      : error.code === 'WEAK_PASSWORD'
        ? error.message
        : (error.message || 'No se ha podido cambiar la contraseña.')
  } finally {
    passwordLoading.value = false
  }
}

function formatDate(value) {
  return new Intl.DateTimeFormat('es-ES', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}
</script>
