<template>
  <PublicLayout>
    <section
      class="flex-1 bg-[#0F172A] flex items-center justify-center px-6 py-12"
    >
      <div class="w-full max-w-md">

        <div class="bg-white rounded-2xl shadow-xl p-8">

          <div class="text-center mb-8">
            <h1 class="text-3xl font-bold text-gray-900">
              Iniciar sesión
            </h1>

            <p class="mt-2 text-gray-600">
              Accede a tu cuenta de AquaGuard
            </p>
          </div>

          <form @submit.prevent="handleSubmit" class="space-y-5">

            <!-- Email -->
            <div>
              <label
                for="email"
                class="block text-sm font-medium text-gray-700 mb-1"
              >
                Email
              </label>

              <input
                id="email"
                v-model="form.email"
                type="email"
                autocomplete="email"
                required
                class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
                placeholder="tu@email.com"
              />
            </div>

            <!-- Password -->
            <div>
              <label
                for="password"
                class="block text-sm font-medium text-gray-700 mb-1"
              >
                Contraseña
              </label>

              <div class="relative">
                <input
                  id="password"
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="current-password"
                  required
                  class="w-full px-4 py-3 pr-20 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  placeholder="Tu contraseña"
                />
                <!-- Show / hide the password, same as the trial sign-up form -->
                <button
                  type="button"
                  class="absolute inset-y-0 right-0 px-3 text-sm font-semibold text-aqua-700 hover:underline"
                  :aria-pressed="showPassword"
                  @click="showPassword = !showPassword"
                >
                  {{ showPassword ? "Ocultar" : "Mostrar" }}
                </button>
              </div>
            </div>

            <!-- Error -->
            <div
              v-if="errorMessage"
              class="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm"
              role="alert"
            >
              {{ errorMessage }}
            </div>

            <!-- Submit -->
            <button
              type="submit"
              :disabled="isLoading"
              class="w-full bg-[#0369A1] text-white font-semibold py-3 rounded-lg hover:bg-[#075985] transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ isLoading ? "Iniciando sesión..." : "Iniciar sesión" }}
            </button>

          </form>

          <p class="text-center text-sm text-gray-600 mt-6">
            ¿No tienes una cuenta?

            <RouterLink
              to="/prueba"
              class="text-[#0369A1] font-semibold hover:underline"
            >
              Prueba 7 días gratis
            </RouterLink>
          </p>

        </div>

      </div>
    </section>
  </PublicLayout>
</template>


<script setup>

import { computed, reactive, ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../../stores/auth.js";
import PublicLayout from "../../layouts/PublicLayout.vue";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const form = reactive({
  email: "",
  password: "",
});

const showPassword = ref(false);

const isLoading = computed(() => authStore.status === "loading");

// Spanish text for the usual login errors; anything else keeps the API message
const errorMessage = computed(() => {
  const error = authStore.error;
  if (!error) return null;

  if (error.code === "INVALID_CREDENTIALS" || error.code === "UNAUTHORIZED") {
    return "Email o contraseña incorrectos.";
  }
  if (error.code === "TOO_MANY_REQUESTS") {
    return "Demasiados intentos, prueba en unos minutos.";
  }
  if (error.code === "NETWORK_ERROR") {
    return "No hemos podido conectar con el servidor. Inténtalo de nuevo.";
  }
  return error.message ?? null;
});

async function handleSubmit() {
  if (isLoading.value) return;

  authStore.clearError();

  try {
    await authStore.login({
      email: form.email,
      password: form.password,
    });

    // Redirect users to their originally requested page when possible.
    const redirect = route.query.redirect;
    const isSafeRedirect =
      typeof redirect === "string" &&
      redirect.startsWith("/") &&
      !redirect.startsWith("//");

    if (isSafeRedirect) {
      await router.replace(redirect);
      return;
    }

    // Redirect users to the home page matching their role.
    await router.replace(
      authStore.isAdmin ? "/admin" : "/dashboard"
    );
  } catch (error) {
    // The authentication store already handles login errors.
  }
}

onMounted(() => {
  authStore.clearError();
});
</script>