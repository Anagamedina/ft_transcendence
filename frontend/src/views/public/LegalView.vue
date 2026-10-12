<template>
  <PublicLayout>
    <div class="max-w-6xl mx-auto px-6 py-12 grid grid-cols-1 lg:grid-cols-[1fr_240px] gap-10">
      <!-- Main content: privacy policy and terms of service on one page -->
      <div class="max-w-3xl">
        <h1 class="text-3xl font-bold text-aqua-900 mb-2">Información legal</h1>
        <p class="text-sm text-slate-500 mb-8">Última actualización: pendiente de acordar con el equipo</p>

        <div class="bg-amber-50 border border-amber-200 text-amber-800 text-sm rounded-lg p-4 mb-10">
          Este contenido es un borrador de referencia y no ha sido validado legalmente.
          No debe considerarse asesoramiento legal hasta su revisión por el equipo del proyecto.
        </div>

        <!-- Privacy policy -->
        <section id="privacidad" class="mb-14 scroll-mt-24">
          <h2 class="text-2xl font-bold text-aqua-900 mb-6">Política de privacidad</h2>

          <section id="privacidad-datos-recogidos" class="mb-10 scroll-mt-24">
            <h3 class="text-lg font-semibold text-aqua-800 mb-3">1. Qué datos recogemos</h3>
            <p class="text-slate-600 mb-3">
              AquaGuard recoge la información necesaria para ofrecer el servicio de monitorización de sensores de agua:
            </p>
            <ul class="list-disc list-inside text-slate-600 space-y-1">
              <li>Datos de cuenta: nombre, email, organización.</li>
              <li>Datos de sensores: lecturas de presión, ubicación, estado y alertas.</li>
              <li>Datos técnicos: dirección IP y registros de acceso, con fines de seguridad.</li>
            </ul>
          </section>

          <section id="privacidad-como-usamos" class="mb-10 scroll-mt-24">
            <h3 class="text-lg font-semibold text-aqua-800 mb-3">2. Cómo usamos los datos</h3>
            <p class="text-slate-600">
              Los datos se utilizan exclusivamente para prestar el servicio: mostrar el estado de tus sensores,
              generar alertas y facilitar la gestión de tu organización. No se venden datos a terceros.
            </p>
          </section>

          <section id="privacidad-con-quien-compartimos" class="mb-10 scroll-mt-24">
            <h3 class="text-lg font-semibold text-aqua-800 mb-3">3. Con quién compartimos los datos</h3>
            <p class="text-slate-600">
              No compartimos tus datos con terceros para fines comerciales. Solo se comparten con proveedores
              técnicos estrictamente necesarios para operar el servicio (por ejemplo, hospedaje de la plataforma),
              y siempre bajo obligación de confidencialidad.
            </p>
          </section>

          <section id="privacidad-conservacion" class="mb-10 scroll-mt-24">
            <h3 class="text-lg font-semibold text-aqua-800 mb-3">4. Conservación de datos</h3>
            <p class="text-slate-600">
              Los datos se conservan mientras la cuenta esté activa. Puedes solicitar su eliminación
              contactando con el responsable del proyecto.
            </p>
          </section>

          <section id="privacidad-tus-derechos" class="mb-10 scroll-mt-24">
            <h3 class="text-lg font-semibold text-aqua-800 mb-3">5. Tus derechos</h3>
            <p class="text-slate-600">
              Puedes solicitar en cualquier momento acceder, corregir o eliminar tus datos personales,
              escribiendo al equipo del proyecto a través de los canales habituales.
            </p>
          </section>

          <section id="privacidad-seguridad" class="mb-10 scroll-mt-24">
            <h3 class="text-lg font-semibold text-aqua-800 mb-3">6. Seguridad</h3>
            <p class="text-slate-600">
              Aplicamos medidas técnicas razonables para proteger tus datos frente a accesos no autorizados,
              aunque ningún sistema puede garantizar seguridad absoluta.
            </p>
          </section>

          <section id="privacidad-menores" class="mb-10 scroll-mt-24">
            <h3 class="text-lg font-semibold text-aqua-800 mb-3">7. Información para menores</h3>
            <p class="text-slate-600">
              AquaGuard no está dirigido a menores de edad y no recogemos intencionadamente datos de menores.
            </p>
          </section>

          <section id="privacidad-cambios" class="mb-10 scroll-mt-24">
            <h3 class="text-lg font-semibold text-aqua-800 mb-3">8. Cambios en esta política</h3>
            <p class="text-slate-600">
              Esta política puede actualizarse. Los cambios relevantes se comunicarán a través de la plataforma.
            </p>
          </section>

          <section id="privacidad-contacto" class="scroll-mt-24">
            <h3 class="text-lg font-semibold text-aqua-800 mb-3">9. Contacto</h3>
            <p class="text-slate-600">
              Para cualquier duda sobre esta política, puedes contactar con el equipo de AquaGuard
              a través de los canales del proyecto.
            </p>
          </section>
        </section>

        <!-- Terms of service -->
        <section id="terminos" class="scroll-mt-24">
          <h2 class="text-2xl font-bold text-aqua-900 mb-6">Términos de servicio</h2>

          <section id="terminos-aceptacion" class="mb-10 scroll-mt-24">
            <h3 class="text-lg font-semibold text-aqua-800 mb-3">1. Aceptación de los términos</h3>
            <p class="text-slate-600">
              Al acceder o usar AquaGuard, aceptas estos términos de servicio. Si no estás de acuerdo,
              no debes utilizar la plataforma.
            </p>
          </section>

          <section id="terminos-uso-servicio" class="mb-10 scroll-mt-24">
            <h3 class="text-lg font-semibold text-aqua-800 mb-3">2. Uso del servicio</h3>
            <p class="text-slate-600 mb-3">
              AquaGuard proporciona monitorización de sensores de presión de agua para detectar fugas.
              Te comprometes a:
            </p>
            <ul class="list-disc list-inside text-slate-600 space-y-1">
              <li>Usar el servicio conforme a la ley y a estos términos.</li>
              <li>No intentar acceder a datos de otras organizaciones sin autorización.</li>
              <li>No interferir con el funcionamiento normal de la plataforma.</li>
            </ul>
          </section>

          <section id="terminos-cuentas" class="mb-10 scroll-mt-24">
            <h3 class="text-lg font-semibold text-aqua-800 mb-3">3. Cuentas de usuario</h3>
            <p class="text-slate-600">
              Eres responsable de mantener la confidencialidad de tus credenciales de acceso
              y de toda la actividad que ocurra bajo tu cuenta.
            </p>
          </section>

          <section id="terminos-propiedad" class="mb-10 scroll-mt-24">
            <h3 class="text-lg font-semibold text-aqua-800 mb-3">4. Propiedad de los datos</h3>
            <p class="text-slate-600">
              Los datos generados por tus sensores (lecturas, alertas, histórico) te pertenecen a ti
              o a tu organización. AquaGuard los procesa únicamente para prestar el servicio.
            </p>
          </section>

          <section id="terminos-disponibilidad" class="mb-10 scroll-mt-24">
            <h3 class="text-lg font-semibold text-aqua-800 mb-3">5. Disponibilidad del servicio</h3>
            <p class="text-slate-600">
              AquaGuard procura mantener el servicio disponible de forma continua, pero no garantiza
              un funcionamiento ininterrumpido. Puede haber mantenimientos o interrupciones puntuales.
            </p>
          </section>

          <section id="terminos-limitacion" class="mb-10 scroll-mt-24">
            <h3 class="text-lg font-semibold text-aqua-800 mb-3">6. Limitación de responsabilidad</h3>
            <p class="text-slate-600">
              AquaGuard es una herramienta de apoyo a la monitorización y no sustituye la inspección
              física de instalaciones. No nos hacemos responsables de daños derivados de fugas no detectadas
              por fallos técnicos ajenos a nuestro control.
            </p>
          </section>

          <section id="terminos-cancelacion" class="mb-10 scroll-mt-24">
            <h3 class="text-lg font-semibold text-aqua-800 mb-3">7. Cancelación de cuenta</h3>
            <p class="text-slate-600">
              Puedes solicitar la cancelación de tu cuenta en cualquier momento contactando con el equipo
              del proyecto. Tras la cancelación, tus datos se tratarán según lo indicado en la
              <a href="#privacidad" class="text-aqua-600 underline hover:text-aqua-900">política de privacidad</a>.
            </p>
          </section>

          <section id="terminos-cambios" class="mb-10 scroll-mt-24">
            <h3 class="text-lg font-semibold text-aqua-800 mb-3">8. Cambios en estos términos</h3>
            <p class="text-slate-600">
              Estos términos pueden actualizarse. Los cambios relevantes se comunicarán a través de la plataforma.
            </p>
          </section>

          <section id="terminos-contacto" class="scroll-mt-24">
            <h3 class="text-lg font-semibold text-aqua-800 mb-3">9. Contacto</h3>
            <p class="text-slate-600">
              Para cualquier duda sobre estos términos, puedes contactar con el equipo de AquaGuard
              a través de los canales del proyecto.
            </p>
          </section>
        </section>
      </div>

      <!-- Side index (desktop only) -->
      <aside class="hidden lg:block">
        <nav aria-label="Índice del documento" class="sticky top-24 text-sm">
          <p class="font-semibold text-aqua-900 mb-2">
            <a href="#privacidad" class="hover:text-aqua-600">Política de privacidad</a>
          </p>
          <ul class="space-y-1.5 text-slate-500 mb-5">
            <li v-for="item in privacyIndex" :key="item.id">
              <a :href="`#privacidad-${item.id}`" class="hover:text-aqua-600">{{ item.label }}</a>
            </li>
          </ul>
          <p class="font-semibold text-aqua-900 mb-2">
            <a href="#terminos" class="hover:text-aqua-600">Términos de servicio</a>
          </p>
          <ul class="space-y-1.5 text-slate-500 mb-5">
            <li v-for="item in termsIndex" :key="item.id">
              <a :href="`#terminos-${item.id}`" class="hover:text-aqua-600">{{ item.label }}</a>
            </li>
          </ul>
          <router-link to="/" class="font-semibold text-aqua-600 hover:text-aqua-900">
            ← Volver al inicio
          </router-link>
        </nav>
      </aside>
    </div>
  </PublicLayout>
</template>

<script setup>
import PublicLayout from "../../layouts/PublicLayout.vue";

// Side index entries; ids match the section ids above (with their prefix)
const privacyIndex = [
  { id: "datos-recogidos", label: "1. Qué datos recogemos" },
  { id: "como-usamos", label: "2. Cómo usamos los datos" },
  { id: "con-quien-compartimos", label: "3. Con quién compartimos" },
  { id: "conservacion", label: "4. Conservación" },
  { id: "tus-derechos", label: "5. Tus derechos" },
  { id: "seguridad", label: "6. Seguridad" },
  { id: "menores", label: "7. Menores" },
  { id: "cambios", label: "8. Cambios" },
  { id: "contacto", label: "9. Contacto" },
];

const termsIndex = [
  { id: "aceptacion", label: "1. Aceptación" },
  { id: "uso-servicio", label: "2. Uso del servicio" },
  { id: "cuentas", label: "3. Cuentas de usuario" },
  { id: "propiedad", label: "4. Propiedad de los datos" },
  { id: "disponibilidad", label: "5. Disponibilidad" },
  { id: "limitacion", label: "6. Limitación de responsabilidad" },
  { id: "cancelacion", label: "7. Cancelación" },
  { id: "cambios", label: "8. Cambios" },
  { id: "contacto", label: "9. Contacto" },
];
</script>