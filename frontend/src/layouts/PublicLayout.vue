<template>
  <div class="min-h-screen flex flex-col">
    <Header :title="headerTitle">
      <template #actions>
        <div class="flex flex-wrap gap-2">
          <RouterLink
            to="/login"
            class="bg-white text-aqua-600 px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg font-semibold hover:bg-gray-100 transition text-xs sm:text-sm"
          >
            Iniciar sesión
          </RouterLink>
          <RouterLink
            to="/registro"
            class="border border-white text-white px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg font-semibold hover:bg-white/10 transition text-xs sm:text-sm"
          >
            Registrarse
          </RouterLink>
        </div>
      </template>
    </Header>

    <main class="flex-1 flex flex-col">
      <slot />
    </main>

    <Footer dark />
  </div>
</template>

<script setup>
import Header from "../components/Header.vue";
import Footer from "../components/Footer.vue";

defineProps({
  headerTitle: { type: String, default: "AquaGuard" },
});
</script>
