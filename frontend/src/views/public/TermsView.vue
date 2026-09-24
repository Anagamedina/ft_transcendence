<template>
  <PublicLayout>
    <div class="max-w-6xl mx-auto px-6 py-12 grid grid-cols-1 lg:grid-cols-[1fr_220px] gap-10">

      <!-- Contenido principal -->
      <div class="max-w-3xl">
        <h1 class="text-2xl font-bold text-aqua-900 mb-2">Terms of Service</h1>
        <p class="text-sm text-gray-400 mb-8">Última actualización: pendiente de acordar con el equipo</p>

        <div class="bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm rounded-lg p-4 mb-10">
          Este contenido es un borrador de referencia y no ha sido validado legalmente.
          No debe considerarse asesoramiento legal hasta su revisión por el equipo del proyecto.
        </div>

        <section id="aceptacion" class="mb-10 scroll-mt-20">
          <h2 class="text-lg font-semibold text-aqua-800 mb-3">1. Aceptación de los términos</h2>
          <p class="text-gray-600">
            Al acceder o usar AquaGuard, aceptas estos términos de servicio. Si no estás de acuerdo,
            no debes utilizar la plataforma.
          </p>
        </section>

        <section id="uso-servicio" class="mb-10 scroll-mt-20">
          <h2 class="text-lg font-semibold text-aqua-800 mb-3">2. Uso del servicio</h2>
          <p class="text-gray-600 mb-3">
            AquaGuard proporciona monitorización de sensores de presión de agua para detectar fugas.
            Te comprometes a:
          </p>
          <ul class="list-disc list-inside text-gray-600 space-y-1">
            <li>Usar el servicio conforme a la ley y a estos términos.</li>
            <li>No intentar acceder a datos de otras organizaciones sin autorización.</li>
            <li>No interferir con el funcionamiento normal de la plataforma.</li>
          </ul>
        </section>

        <section id="cuentas" class="mb-10 scroll-mt-20">
          <h2 class="text-lg font-semibold text-aqua-800 mb-3">3. Cuentas de usuario</h2>
          <p class="text-gray-600">
            Eres responsable de mantener la confidencialidad de tus credenciales de acceso
            y de toda la actividad que ocurra bajo tu cuenta.
          </p>
        </section>

        <section id="propiedad" class="mb-10 scroll-mt-20">
          <h2 class="text-lg font-semibold text-aqua-800 mb-3">4. Propiedad de los datos</h2>
          <p class="text-gray-600">
            Los datos generados por tus sensores (lecturas, alertas, histórico) te pertenecen a ti
            o a tu organización. AquaGuard los procesa únicamente para prestar el servicio.
          </p>
        </section>

        <section id="disponibilidad" class="mb-10 scroll-mt-20">
          <h2 class="text-lg font-semibold text-aqua-800 mb-3">5. Disponibilidad del servicio</h2>
          <p class="text-gray-600">
            AquaGuard procura mantener el servicio disponible de forma continua, pero no garantiza
            un funcionamiento ininterrumpido. Puede haber mantenimientos o interrupciones puntuales.
          </p>
        </section>

        <section id="limitacion" class="mb-10 scroll-mt-20">
          <h2 class="text-lg font-semibold text-aqua-800 mb-3">6. Limitación de responsabilidad</h2>
          <p class="text-gray-600">
            AquaGuard es una herramienta de apoyo a la monitorización y no sustituye la inspección
            física de instalaciones. No nos hacemos responsables de daños derivados de fugas no detectadas
            por fallos técnicos ajenos a nuestro control.
          </p>
        </section>

        <section id="cancelacion" class="mb-10 scroll-mt-20">
          <h2 class="text-lg font-semibold text-aqua-800 mb-3">7. Cancelación de cuenta</h2>
          <p class="text-gray-600">
            Puedes solicitar la cancelación de tu cuenta en cualquier momento contactando con el equipo
            del proyecto. Tras la cancelación, tus datos se tratarán según lo indicado en la Política de Privacidad.
          </p>
        </section>

        <section id="cambios" class="mb-10 scroll-mt-20">
          <h2 class="text-lg font-semibold text-aqua-800 mb-3">8. Cambios en estos términos</h2>
          <p class="text-gray-600">
            Estos términos pueden actualizarse. Los cambios relevantes se comunicarán a través de la plataforma.
          </p>
        </section>

        <section id="contacto" class="mb-4 scroll-mt-20">
          <h2 class="text-lg font-semibold text-aqua-800 mb-3">9. Contacto</h2>
          <p class="text-gray-600">
            Para cualquier duda sobre estos términos, puedes contactar con el equipo de AquaGuard
            a través de los canales del proyecto.
          </p>
        </section>
      </div>

      <!-- Índice lateral -->
      <aside class="hidden lg:block">
        <nav class="sticky top-24 text-sm">
          <p class="font-semibold text-aqua-900 mb-3">En este documento</p>
          <ul class="space-y-2 text-gray-500 mb-4">
            <li><a href="#aceptacion" class="hover:text-aqua-700">1. Aceptación</a></li>
            <li><a href="#uso-servicio" class="hover:text-aqua-700">2. Uso del servicio</a></li>
            <li><a href="#cuentas" class="hover:text-aqua-700">3. Cuentas de usuario</a></li>
            <li><a href="#propiedad" class="hover:text-aqua-700">4. Propiedad de los datos</a></li>
            <li><a href="#disponibilidad" class="hover:text-aqua-700">5. Disponibilidad</a></li>
            <li><a href="#limitacion" class="hover:text-aqua-700">6. Limitación de responsabilidad</a></li>
            <li><a href="#cancelacion" class="hover:text-aqua-700">7. Cancelación</a></li>
            <li><a href="#cambios" class="hover:text-aqua-700">8. Cambios</a></li>
            <li><a href="#contacto" class="hover:text-aqua-700">9. Contacto</a></li>
          </ul>
          <router-link to="/" class="block text-aqua-900 font-bold underline hover:text-aqua-700">
            ← Volver al inicio
          </router-link>
        </nav>
      </aside>
    </div>
  </PublicLayout>
</template>

<script setup>
import PublicLayout from '../../layouts/PublicLayout.vue'
</script>
