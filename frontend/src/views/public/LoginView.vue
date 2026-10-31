<template>
  <PublicLayout>
    <section
      class="flex-1 bg-gradient-to-b from-aqua-100 to-aqua-50 flex items-center justify-center px-4 py-12 sm:px-6 md:py-16"
    >
      <div class="w-full max-w-md">
        <div class="bg-white border border-aqua-100 rounded-2xl p-6 sm:p-8 shadow-[0_16px_40px_theme(colors.aqua.600/10%)]">
          <div class="text-center mb-8">
            <h1 class="text-3xl font-bold text-aqua-900">Iniciar sesión</h1>

            <p class="mt-2 text-slate-600">Accede a tu cuenta de AquaGuard</p>
          </div>

          <form @submit.prevent="handleSubmit" class="space-y-5">
            <div>
              <label
                for="email"
                class="block text-sm font-medium text-slate-700 mb-1"
              >
                Email
              </label>

              <input
                id="email"
                v-model="form.email"
                type="email"
                :maxlength="FIELD_LIMITS.email"
                autocomplete="email"
                required
                class="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-aqua-400"
                placeholder="tu@email.com"
              />
            </div>

            <div>
              <label
                for="password"
                class="block text-sm font-medium text-slate-700 mb-1"
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
                  :aria-invalid="Boolean(passwordError)"
                  :aria-describedby="passwordError ? 'password-error' : undefined"
                  class="w-full px-4 py-3 pr-20 border rounded-lg focus:outline-none focus:ring-2 focus:ring-aqua-400"
                  :class="passwordError ? 'border-danger' : 'border-slate-300'"
                  placeholder="Tu contraseña"
                  @input="passwordError = null"
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
              <p
                v-if="passwordError"
                id="password-error"
                class="mt-1 text-sm text-danger-dark"
              >
                {{ passwordError }}
              </p>
            </div>

            <!-- Error -->
            <div
              v-if="errorMessage"
              class="bg-danger-light border border-danger text-danger-dark rounded-lg p-3 text-sm"
              role="alert"
            >
              {{ errorMessage }}
            </div>

            <!-- Submit -->
            <button
              type="submit"
              :disabled="isLoading"
              class="w-full bg-aqua-600 text-white font-semibold py-3 rounded-lg hover:bg-aqua-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ isLoading ? "Iniciando sesión..." : "Iniciar sesión" }}
            </button>
          </form>

          <p class="text-center text-sm text-slate-600 mt-6">
            ¿No tienes una cuenta?

            <RouterLink
              to="/prueba"
              class="text-aqua-700 font-semibold hover:underline"
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
import { FIELD_LIMITS } from "../../utils/limits.js";
import { loginPasswordProblem } from "../../utils/passwords.js";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const form = reactive({
  email: "",
  password: "",
});

const showPassword = ref(false);
const passwordError = ref(null);

const isLoading = computed(() => authStore.status === "loading");

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

  // Only "something was typed": the password goes to the API as typed,
  // without trimming, so " clave" does not log in as "clave".
  passwordError.value = loginPasswordProblem(form.password);
  if (passwordError.value) return;

  try {
    await authStore.login({
      email: form.email,
      password: form.password,
    });

    // Redirect to the requested page if it is safe.
    const redirect = route.query.redirect;

    const isSafeRedirect =
      typeof redirect === "string" &&
      redirect.startsWith("/") &&
      !redirect.startsWith("//");

    if (isSafeRedirect) {
      await router.replace(redirect);
      return;
    }

    // Redirect according to the user's role.
    if (authStore.isAdmin) {
      await router.replace("/admin");
    } else if (authStore.isClient) {
      await router.replace("/app");
    } else {
      await router.replace("/");
    }
  } catch (error) {
    // The authentication store already handles login errors.
  }
}

onMounted(() => {
  authStore.clearError();
});
</script>
