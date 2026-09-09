<template>
  <MainLayout header-title="AquaGuard" sidebar-app-name="AquaGuard">
    <!--
      This file is the "integration layer": it is the only place that knows
      about the store. SensorDetail.vue (the pure component) only receives
      props. When Lylia wires up the real API, this is the only file that
      should need to change.
    -->
    <SensorDetail :sensor="sensor" />

    <router-link
      to="/test"
      class="inline-block mt-4 text-aqua-600 hover:underline"
    >
      &larr; Volver
    </router-link>
  </MainLayout>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import MainLayout from '../../layouts/MainLayout.vue'
import SensorDetail from '../../components/SensorDetail.vue'
import { useSensorsStore } from '../../stores/sensors'

const route = useRoute()
const sensorsStore = useSensorsStore()

const sensor = computed(() =>
  sensorsStore.sensors.find(s => String(s.id) === route.params.id)
)
</script>
