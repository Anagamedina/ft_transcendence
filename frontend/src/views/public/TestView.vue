<template>
  <div class="p-8">
    <Header title="Prueba de Componentes" />
    
    <div class="flex gap-4 mt-4">
      <Sidebar appName="AquaGuard Test" />
      
      <Card 
        title="Mi Sensor"
        description="Presión: 3.5 bar"
        buttonText="Ver detalles"
        @click="handleClick"
      />
    </div>
  </div>
</template>

<script setup>
import Header from '../../components/Header.vue'
import Sidebar from '../../components/Sidebar.vue'
import Card from '../../components/Card.vue'

const handleClick = () => {
  console.log('¡Botón clickeado!')
}
</script>