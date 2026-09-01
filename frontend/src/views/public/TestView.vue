<template>
  <MainLayout header-title="AquaGuard componentes compartidos👌​" sidebar-app-name="AquaGuard Test">
    <Card 
      title="Mi Sensor"
      description="Presión: 3.5 bar"
      buttonText="Ver detalles"
      @click="handleClick"
    />

    <button
      @click="modalAbierto = true"
      class="mt-4 border-2 border-aqua-600 text-aqua-600 px-4 py-2 rounded-lg hover:bg-aqua-50 transition"
    >
      Abrir modal
    </button>

    <Modal :show="modalAbierto" title="Prueba de Modal" @close="modalAbierto = false">
      <p>Este es el contenido de prueba del modal.</p>

      <template #footer>
        <button
          @click="modalAbierto = false"
          class="px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-50 transition"
        >
          Cancelar
        </button>
        <button
          @click="modalAbierto = false"
          class="px-4 py-2 rounded-lg bg-aqua-600 text-white hover:bg-aqua-800 transition"
        >
          Confirmar
        </button>
      </template>
    </Modal>
  </MainLayout>
</template>

<script setup>
import { ref } from 'vue'
import MainLayout from '../../layouts/MainLayout.vue'
import Card from '../../components/Card.vue'
import Modal from '../../components/Modal.vue'

const modalAbierto = ref(false)

const handleClick = () => {
  console.log('¡Botón clickeado!')
}
</script>