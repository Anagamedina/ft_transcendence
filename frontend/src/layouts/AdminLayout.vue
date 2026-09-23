<!--
  ADMIN LAYOUT
  Shared structure for admin pages: Header, Sidebar, Footer and a slot for page content.
-->
  
<template>
  <div class="min-h-screen min-w-[320px] flex flex-col">
    <Header title="AquaGuard · Admin">
      <template #actions>
        <button
          class="bg-white text-aqua-600 px-4 py-2 rounded-lg font-semibold hover:bg-gray-100 transition shrink-0"
        >
          Cerrar sesión
        </button>
      </template>
    </Header>

    <div class="flex flex-1 overflow-hidden">
      <Sidebar appName="Admin" />

      <main class="flex-1 overflow-y-auto bg-slate-50 p-6">
        <slot />
      </main>
    </div>

    <Footer />
  </div>
</template>

<script setup>
import Header from "../components/Header.vue";
import Sidebar from "../components/Sidebar.vue";
import Footer from "../components/Footer.vue";
</script>