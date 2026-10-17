<template>
  <div class="space-y-6">
    <h1 class="text-3xl font-bold text-gray-900">Mi cuenta</h1>

    <!-- Two columns on desktop, one on mobile. Extra cards come from the slots:
         the client view adds Suscripción and Privacidad, the admin view adds nothing. -->
    <div class="grid items-start gap-6 lg:grid-cols-2">
      <section class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm" aria-labelledby="profile-title">
        <h2 id="profile-title" class="mb-4 text-lg font-bold text-gray-800">Datos personales</h2>
        <form class="space-y-4" @submit.prevent="saveProfile">
          <div>
            <label for="account-name" class="block text-sm font-medium text-gray-700">Nombre</label>
            <input
              id="account-name"
              v-model="name"
              required
              maxlength="120"
              autocomplete="name"
              class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
            />
          </div>
          <div>
            <label for="account-email" class="block text-sm font-medium text-gray-700">Email</label>
            <input
              id="account-email"
              :value="authStore.user?.email"
              readonly
              aria-describedby="account-email-hint"
              class="mt-1 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-gray-500"
            />
            <p id="account-email-hint" class="mt-1 text-xs text-gray-500">El email no se puede cambiar.</p>
          </div>
          <p class="text-xs text-gray-500">
            <template v-if="authStore.isAdmin">Rol: Administrador · </template>
            Último acceso: {{ formatDateTime(authStore.lastLoginAt) }}
          </p>
          <p v-if="profileError" class="text-sm text-red-700" role="alert">{{ profileError }}</p>
          <p v-if="profileSaved" class="text-sm text-green-700" role="status">Datos actualizados.</p>
          <button type="submit" :disabled="profileLoading" class="rounded-lg bg-aqua-600 px-4 py-2 font-semibold text-white disabled:opacity-50">
            {{ profileLoading ? 'Guardando…' : 'Guardar cambios' }}
          </button>
        </form>
      </section>

      <slot name="after-profile" />

      <section class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm" aria-labelledby="password-title">
        <h2 id="password-title" class="mb-4 text-lg font-bold text-gray-800">Cambiar contraseña</h2>
        <form class="space-y-4" @submit.prevent="savePassword">
          <div v-for="field in passwordFields" :key="field.key">
            <label :for="`account-${field.key}`" class="block text-sm font-medium text-gray-700">{{ field.label }}</label>
            <input
              :id="`account-${field.key}`"
              v-model="password[field.key]"
              type="password"
              required
              maxlength="128"
              :minlength="field.key === 'current_password' ? undefined : PASSWORD_MIN_LENGTH"
              :autocomplete="field.key === 'current_password' ? 'current-password' : 'new-password'"
              :aria-describedby="field.key === 'new_password' ? 'account-password-hint' : undefined"
              class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
            />
            <p v-if="field.key === 'new_password'" id="account-password-hint" class="mt-1 text-xs text-gray-500">
              Mínimo {{ PASSWORD_MIN_LENGTH }} caracteres, la misma regla que el registro.
            </p>
          </div>
          <p v-if="passwordError" class="text-sm text-red-700" role="alert">{{ passwordError }}</p>
          <p
            v-if="passwordSaved"
            role="status"
            class="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800"
          >
            Contraseña cambiada. La próxima vez entra con la nueva.
          </p>
          <button type="submit" :disabled="passwordLoading" class="rounded-lg bg-aqua-600 px-4 py-2 font-semibold text-white disabled:opacity-50">
            {{ passwordLoading ? 'Actualizando…' : 'Cambiar contraseña' }}
          </button>
        </form>
      </section>

      <slot name="after-password" />
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useAuthStore } from '../stores/auth'
import { formatDateTime } from '../composables/useFormat'

// Same rule as the sign-up form (/prueba) and the backend (B10)
const PASSWORD_MIN_LENGTH = 12

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
  { key: 'new_password', label: 'Contraseña nueva' },
  { key: 'confirmation', label: 'Repite la contraseña nueva' },
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
  passwordError.value = ''
  passwordSaved.value = false
  if (password.value.new_password !== password.value.confirmation) {
    passwordError.value = 'Las contraseñas nuevas no coinciden.'
    return
  }
  passwordLoading.value = true
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
</script>
