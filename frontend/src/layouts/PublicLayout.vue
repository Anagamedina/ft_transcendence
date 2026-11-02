<template>
  <div class="min-h-screen flex flex-col">
    <Header :title="headerTitle" light>
      <template #actions>
        <nav aria-label="Navegación principal" class="flex gap-2">
          <!-- F29: with a session, offer to go back to the panel of the role -->
          <RouterLink
            v-if="authStore.isAuthenticated"
            :to="panelPath"
            class="bg-aqua-600 text-white px-4 py-2 rounded-lg font-semibold text-sm hover:bg-aqua-700 transition"
          >
            Ir a mi panel
          </RouterLink>
          <template v-else>
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
          </template>
        </nav>
      </template>
    </Header>

    <main class="flex-1 flex flex-col">
      <slot />
    </main>
    <Footer />
  </div>
</template>

<script setup>
import { computed, onMounted } from "vue";
import Header from "../components/Header.vue";
import Footer from "../components/Footer.vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "../stores/auth";

defineProps({
  headerTitle: { type: String, default: "AquaGuard" },
});

const authStore = useAuthStore();

const panelPath = computed(() => (authStore.isAdmin ? "/admin" : "/app"));

const route = useRoute();

// Pages that offer "Ir a mi panel" (plus the 404 page, whatever its URL).
// The router does not check the session on them, so ask for it here
// (without a session the backend answers 200 with user null, no 401). Only
// on these pages: on /registro the answer could arrive after a sign-up and
// clear the user that was just created.
const SESSION_AWARE_PATHS = ["/", "/legal", "/status"];

onMounted(() => {
  if (SESSION_AWARE_PATHS.includes(route.path) || route.name === "NotFound") {
    authStore.initializeAuth();
  }
});
</script>
