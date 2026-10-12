<template>
  <div class="min-h-screen min-w-[320px] flex flex-col">
    <!-- pl-12 on mobile: room for the Sidebar menu button, which is fixed at the top left -->
    <Header :title="headerTitle" class="pl-12 md:pl-0" />

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
import Header from "../components/Header.vue";
import Sidebar from "../components/Sidebar.vue";
import Footer from "../components/Footer.vue";

defineProps({
  headerTitle: { type: String, default: "AquaGuard" },
  sidebarAppName: { type: String, default: "AquaGuard" },
});
</script>
