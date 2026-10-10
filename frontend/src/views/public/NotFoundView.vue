<!-- Displays a 404 page when the requested route does not exist. -->

<template>
  <div class="min-h-screen flex flex-col items-center justify-center bg-gray-100 p-6">
    <h1 class="text-6xl font-bold text-gray-800">404</h1>

    <p class="mt-4 text-xl text-gray-600">
      Página no encontrada
    </p>

    <p class="mt-2 text-gray-500">
      La dirección que has introducido no existe.
    </p>

    <RouterLink
      to="/"
      class="mt-6 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
    >
      Volver al inicio
    </RouterLink>
  </div>
</template>