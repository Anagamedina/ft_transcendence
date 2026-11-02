<!--
  CLIENT ALERTS VIEW (F21)
  /app/alerts: every alert of the client, all buildings (menu "Alertas").
  The content is ClientAlertsPanel, shared with the "Alertas" tab of the
  building page (F25), which shows only that building.
-->

<template>
  <div class="mx-auto max-w-7xl space-y-6">
    <header>
      <h1 class="text-2xl font-bold text-slate-900">Alertas</h1>
      <p class="mt-1 text-sm text-slate-600">
        AquaGuard te avisa, tú lo arreglas y nosotros revisamos las lecturas
        para cerrarlo.
      </p>
    </header>

    <ClientAlertsPanel />
  </div>
</template>

<script setup>
import ClientAlertsPanel from "../../components/ClientAlertsPanel.vue";
</script>
