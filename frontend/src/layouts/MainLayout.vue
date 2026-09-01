<template>
  <div class="min-h-screen flex flex-col">
    <Header :title="headerTitle" />

    <div class="flex flex-1 overflow-hidden">
      <Sidebar :appName="sidebarAppName" />

      <main class="flex-1 overflow-y-auto bg-slate-50 p-6">
        <slot />
      </main>
    </div>

    <Footer />
  </div>
</template>

<script setup>
import Header from '../components/Header.vue'
import Sidebar from '../components/Sidebar.vue'
import Footer from '../components/Footer.vue'

defineProps({
  headerTitle: { type: String, default: 'AquaGuard' },
  sidebarAppName: { type: String, default: 'AquaGuard' }
})
</script>