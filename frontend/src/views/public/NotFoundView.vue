<!-- Displays a 404 page when the requested route does not exist. -->

<template>
  <PublicLayout>
    <section
      class="flex-1 bg-gradient-to-b from-aqua-100 to-aqua-50 flex flex-col items-center justify-center text-center px-6 py-16"
    >
      <h1 class="text-6xl font-bold text-aqua-900">404</h1>

      <p class="mt-4 text-xl text-slate-700">Página no encontrada</p>

      <p class="mt-2 text-slate-600">
        La dirección que has introducido no existe.
      </p>

      <RouterLink
        to="/"
        class="mt-6 px-5 py-3 bg-aqua-600 text-white font-semibold rounded-lg hover:bg-aqua-700 transition"
      >
        Volver al inicio
      </RouterLink>
    </section>
  </PublicLayout>
</template>

<script setup>
import PublicLayout from "../../layouts/PublicLayout.vue";
</script>
