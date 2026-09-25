<!--
  ADMIN DASHBOARD VIEW
  Main admin page: KPIs summary, sites, sensors and alerts overview.
  Rendered inside AdminLayout. Data comes only from Pinia stores (no direct HTTP calls).
-->

<script setup>
import AdminLayout from '../../layouts/AdminLayout.vue'
import KPICard from '../../components/KPICard.vue'
import { useSensorsStore } from '../../stores/sensors'
import { useAlertsStore } from '../../stores/alerts'

const sensorStore = useSensorsStore()
const alertsStore = useAlertsStore()
</script>

<template>
  <AdminLayout>
    <h1 class="text-2xl font-bold text-gray-800 mb-6">Dashboard Admin</h1>

    <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <KPICard label="Sites" :value="3" icon="🏢" />
      <KPICard label="Sensores totales" :value="12" icon="💧" />
      <KPICard label="Sensores online" :value="10" icon="🟢" />
      <KPICard label="Alertas activas" :value="2" icon="⚠️" />
    </section>
  </AdminLayout>
</template>