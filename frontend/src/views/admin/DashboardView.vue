<!--
  ADMIN DASHBOARD VIEW
  Main admin page: KPIs summary, sites, sensors and alerts overview.
  Rendered inside AdminLayout. Data comes only from Pinia stores (no direct HTTP calls).
-->

<script setup>
import AdminLayout from '../../layouts/AdminLayout.vue'
import { useSensorsStore } from '../../stores/sensors'
import { useAlertsStore } from '../../stores/alerts'

const sensorStore = useSensorsStore()
const alertsStore = useAlertsStore()
</script>

<template>
  <AdminLayout>
    <h1>Dashboard Admin</h1>
  </AdminLayout>
</template>