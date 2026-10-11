<template>
  <div class="min-h-screen flex flex-col">
    <Header :title="headerTitle" light>
      <template #actions>
        <nav aria-label="Navegación principal" class="flex gap-2">
          <RouterLink
            to="/login"
            class="border border-aqua-600 text-aqua-600 px-4 py-2 rounded-lg font-semibold text-sm hover:bg-aqua-50 transition"
            exact-active-class="ring-2 ring-offset-2 ring-aqua-600"
          >
            Entrar
          </RouterLink>
          <RouterLink
            to="/prueba"
            class="bg-aqua-600 text-white px-4 py-2 rounded-lg font-semibold text-sm hover:bg-aqua-700 transition"
            exact-active-class="ring-2 ring-offset-2 ring-aqua-600"
          >
            Prueba 7 días
          </RouterLink>
        </nav>
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
