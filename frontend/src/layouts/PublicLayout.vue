<template>
  <div class="min-h-screen flex flex-col">
    <Header :title="headerTitle" />

    <main class="flex-1 bg-white">
      <slot />
    </main>

    <Footer />
  </div>
</template>

<script setup>
import Header from '../components/Header.vue'
import Footer from '../components/Footer.vue'

defineProps({
  headerTitle: { type: String, default: 'AquaGuard' }
})
</script>