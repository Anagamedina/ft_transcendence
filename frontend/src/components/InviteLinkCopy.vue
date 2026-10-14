<!--
  INVITE LINK COPY
  Shows an invitation link (B4) in a read-only field with a "Copiar enlace" button
  and its expiry date. The admin sends the link to the new user, who opens it to sign up.
  Usage:
    <InviteLinkCopy :link="invitation.link" :expires-at="invitation.expires_at" />
-->

<template>
  <div class="flex flex-col gap-2">
    <div class="flex flex-col gap-2 sm:flex-row">
      <label :for="inputId" class="sr-only">Enlace de invitación</label>
      <input
        :id="inputId"
        ref="input"
        type="text"
        readonly
        :value="link"
        class="min-w-0 flex-1 rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 font-mono text-sm text-gray-800"
        @focus="$event.target.select()"
      />
      <button
        type="button"
        class="min-h-10 min-w-36 rounded-lg bg-aqua-600 px-4 text-sm font-semibold text-white hover:bg-aqua-700"
        @click="copy"
      >
        {{ copied ? 'Copiado' : 'Copiar enlace' }}
      </button>
    </div>

    <p v-if="expiresAt" class="text-xs text-gray-500">Caduca el {{ formatDate(expiresAt) }}</p>

    <!-- role="status": screen readers announce the result without moving the focus -->
    <p role="status" class="text-sm" :class="failed ? 'text-red-700' : 'text-green-700'">
      {{ message }}
    </p>
  </div>
</template>

<script setup>
import { ref, useId, onBeforeUnmount } from 'vue'
import { useFormat } from '../composables/useFormat'

const props = defineProps({
  link: { type: String, required: true },
  // ISO date when the invitation stops working (INVITATION_TTL_DAYS after it is created)
  expiresAt: { type: String, default: '' },
})

const inputId = `invite-link-${useId()}`
const input = ref(null)

const copied = ref(false)
const failed = ref(false)
const message = ref('')
let resetTimer = null

// '21 oct 2026'
const { formatDate } = useFormat()

// Old way to copy, for browsers or http pages where navigator.clipboard is not available
function copyWithSelection() {
  input.value.select()
  return document.execCommand('copy')
}

async function copy() {
  let ok = false
  try {
    // Clipboard API: only available on https and localhost
    await navigator.clipboard.writeText(props.link)
    ok = true
  } catch {
    ok = copyWithSelection()
  }

  failed.value = !ok
  copied.value = ok
  message.value = ok
    ? 'Enlace copiado. Pégalo en un email o un mensaje.'
    : 'No se ha podido copiar. Selecciona el enlace y cópialo con Ctrl+C.'

  if (!ok) input.value.select()

  // The button goes back to "Copiar enlace" after a few seconds
  clearTimeout(resetTimer)
  resetTimer = setTimeout(() => (copied.value = false), 3000)
}

onBeforeUnmount(() => clearTimeout(resetTimer))
</script>
