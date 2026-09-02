<template>
	<MainLayout header-title="AquaGuard Fronted issue #4 ​" sidebar-app-name="AquaGuard Test">
		<Card 
			title="Mi Sensor"
			description="Presión: 3.5 bar"
			buttonText="Ver detalles"
			@click="handleClick"
		/>
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
			<SensorCard name="Sensor Cocina" location="Planta baja" statusKey="normal" :value="2.3" unit="bar" class="mt-4" />
			<SensorCard name="Sensor Baño 2" location="Planta 1" statusKey="warning" :value="4.8" unit="bar" class="mt-4" />
			<SensorCard name="Sensor Terraza" location="Ático" statusKey="critical" :value="0.4" unit="bar" class="mt-4" />
			<SensorCard name="Sensor Sótano" location="Planta -1" statusKey="offline" class="mt-4" />
		</div>

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
import SensorCard from '../../components/SensorCard.vue'

const modalAbierto = ref(false)

const handleClick = () => {
	console.log('¡Botón clickeado!')
}
</script>
