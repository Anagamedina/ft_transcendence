<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50"
        @click.self="close"
      >
        <div
          class="bg-white rounded-xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto"
          role="dialog"
          aria-modal="true"
        >
          <!-- Cabecera -->
          <div class="flex justify-between items-center border-b border-aqua-100 px-6 py-4">
            <slot name="header">
              <h3 class="text-lg font-bold text-aqua-900">{{ title }}</h3>
            </slot>
            <button
              class="text-gray-400 hover:text-aqua-600 text-2xl leading-none transition"
              @click="close"
              aria-label="Cerrar"
            >
              ✕
            </button>
          </div>

          <!-- Cuerpo -->
          <div class="px-6 py-4">
            <slot />
          </div>

          <!-- Pie (opcional) -->
          <div v-if="$slots.footer" class="flex justify-end gap-3 border-t border-aqua-100 px-6 py-4">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'

const props = defineProps({
  show: { type: Boolean, default: false },
  title: { type: String, default: '' }
})

const emit = defineEmits(['close'])

function close() {
  emit('close')
}

function handleEsc(e) {
  if (e.key === 'Escape' && props.show) close()
}

onMounted(() => document.addEventListener('keydown', handleEsc))
onUnmounted(() => document.removeEventListener('keydown', handleEsc))
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>