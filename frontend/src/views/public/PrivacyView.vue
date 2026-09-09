<template>
  <PublicLayout>
    <div class="max-w-6xl mx-auto px-6 py-12 grid grid-cols-1 lg:grid-cols-[1fr_220px] gap-10">

      <!-- Contenido principal -->
      <div class="max-w-3xl">
        <h1 class="text-2xl font-bold text-aqua-900 mb-2">Privacy Policy</h1>
        <p class="text-sm text-gray-400 mb-8">Última actualización: pendiente de acordar con el equipo</p>

        <div class="bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm rounded-lg p-4 mb-10">
          Este contenido es un borrador de referencia y no ha sido validado legalmente.
          No debe considerarse asesoramiento legal hasta su revisión por el equipo del proyecto.
        </div>

        <section id="datos-recogidos" class="mb-10 scroll-mt-20">
          <h2 class="text-lg font-semibold text-aqua-800 mb-3">1. Qué datos recogemos</h2>
          <p class="text-gray-600 mb-3">
            AquaGuard recoge la información necesaria para ofrecer el servicio de monitorización de sensores de agua:
          </p>
          <ul class="list-disc list-inside text-gray-600 space-y-1">
            <li>Datos de cuenta: nombre, email, organización.</li>
            <li>Datos de sensores: lecturas de presión, ubicación, estado y alertas.</li>
            <li>Datos técnicos: dirección IP y registros de acceso, con fines de seguridad.</li>
          </ul>
        </section>

        <section id="como-usamos" class="mb-10 scroll-mt-20">
          <h2 class="text-lg font-semibold text-aqua-800 mb-3">2. Cómo usamos los datos</h2>
          <p class="text-gray-600">
            Los datos se utilizan exclusivamente para prestar el servicio: mostrar el estado de tus sensores,
            generar alertas y facilitar la gestión de tu organización. No se venden datos a terceros.
          </p>
        </section>

        <section id="con-quien-compartimos" class="mb-10 scroll-mt-20">
          <h2 class="text-lg font-semibold text-aqua-800 mb-3">3. Con quién compartimos los datos</h2>
          <p class="text-gray-600">
            No compartimos tus datos con terceros para fines comerciales. Solo se comparten con proveedores
            técnicos estrictamente necesarios para operar el servicio (por ejemplo, hospedaje de la plataforma),
            y siempre bajo obligación de confidencialidad.
          </p>
        </section>

        <section id="conservacion" class="mb-10 scroll-mt-20">
          <h2 class="text-lg font-semibold text-aqua-800 mb-3">4. Conservación de datos</h2>
          <p class="text-gray-600">
            Los datos se conservan mientras la cuenta esté activa. Puedes solicitar su eliminación
            contactando con el responsable del proyecto.
          </p>
        </section>

        <section id="tus-derechos" class="mb-10 scroll-mt-20">
          <h2 class="text-lg font-semibold text-aqua-800 mb-3">5. Tus derechos</h2>
          <p class="text-gray-600">
            Puedes solicitar en cualquier momento acceder, corregir o eliminar tus datos personales,
            escribiendo al equipo del proyecto a través de los canales habituales.
          </p>
        </section>

        <section id="seguridad" class="mb-10 scroll-mt-20">
          <h2 class="text-lg font-semibold text-aqua-800 mb-3">6. Seguridad</h2>
          <p class="text-gray-600">
            Aplicamos medidas técnicas razonables para proteger tus datos frente a accesos no autorizados,
            aunque ningún sistema puede garantizar seguridad absoluta.
          </p>
        </section>

        <section id="menores" class="mb-10 scroll-mt-20">
          <h2 class="text-lg font-semibold text-aqua-800 mb-3">7. Información para menores</h2>
          <p class="text-gray-600">
            AquaGuard no está dirigido a menores de edad y no recogemos intencionadamente datos de menores.
          </p>
        </section>

        <section id="cambios" class="mb-10 scroll-mt-20">
          <h2 class="text-lg font-semibold text-aqua-800 mb-3">8. Cambios en esta política</h2>
          <p class="text-gray-600">
            Esta política puede actualizarse. Los cambios relevantes se comunicarán a través de la plataforma.
          </p>
        </section>

        <section id="contacto" class="mb-4 scroll-mt-20">
          <h2 class="text-lg font-semibold text-aqua-800 mb-3">9. Contacto</h2>
          <p class="text-gray-600">
            Para cualquier duda sobre esta política, puedes contactar con el equipo de AquaGuard
            a través de los canales del proyecto.
          </p>
        </section>
      </div>

      <!-- Índice lateral -->
      <aside class="hidden lg:block">
        <nav class="sticky top-24 text-sm">
          <p class="font-semibold text-aqua-900 mb-3">En este documento</p>
          <ul class="space-y-2 text-gray-500">
            <li><a href="#datos-recogidos" class="hover:text-aqua-700">1. Qué datos recogemos</a></li>
            <li><a href="#como-usamos" class="hover:text-aqua-700">2. Cómo usamos los datos</a></li>
            <li><a href="#con-quien-compartimos" class="hover:text-aqua-700">3. Con quién compartimos</a></li>
            <li><a href="#conservacion" class="hover:text-aqua-700">4. Conservación</a></li>
            <li><a href="#tus-derechos" class="hover:text-aqua-700">5. Tus derechos</a></li>
            <li><a href="#seguridad" class="hover:text-aqua-700">6. Seguridad</a></li>
            <li><a href="#menores" class="hover:text-aqua-700">7. Menores</a></li>
            <li><a href="#cambios" class="hover:text-aqua-700">8. Cambios</a></li>
            <li><a href="#contacto" class="hover:text-aqua-700">9. Contacto</a></li>
          </ul>
        </nav>
      </aside>

    </div>
  </PublicLayout>
</template>

<script setup>
import PublicLayout from '../../layouts/PublicLayout.vue'
</script>