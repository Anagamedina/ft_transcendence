<template>
  <PublicLayout>
    <div
      class="max-w-6xl mx-auto px-6 py-12 grid grid-cols-1 lg:grid-cols-[1fr_240px] gap-10"
    >
      <!-- Main content: privacy policy and terms of service on one page -->
      <div class="max-w-3xl min-w-0">
        <h1 class="text-3xl font-bold text-aqua-900 mb-2">Información legal</h1>
        <p class="text-sm text-slate-600 mb-8">
          Versión {{ LEGAL_VERSION }} · última actualización: {{ LAST_UPDATED }}
        </p>

        <!-- Kept on purpose until the texts get a legal review (#195) -->
        <div
          role="note"
          class="bg-warning-light border border-warning/40 text-warning-dark text-sm rounded-lg p-4 mb-8"
        >
          AquaGuard es un proyecto académico de 42 Barcelona (ft_transcendence).
          Este texto describe cómo funciona la aplicación, pero es un borrador
          que no ha pasado una revisión jurídica.
        </div>

        <!-- Short summary before the full text -->
        <div class="bg-aqua-50 border border-aqua-100 rounded-lg p-5 mb-12">
          <h2 class="font-semibold text-aqua-900 mb-3">En 30 segundos</h2>
          <ul class="list-disc pl-5 text-slate-700 space-y-1.5">
            <li v-for="line in summary" :key="line">{{ line }}</li>
          </ul>
        </div>

        <!-- One tab per document. #privacidad and #terminos (footer and forms) open the right tab -->
        <!-- The anchor sits on the tab bar, so #privacidad / #terminos show the tabs too -->
        <div :id="activeTab" class="scroll-mt-24">
          <Tabs v-model="activeTab" :tabs="TABS" label="Documentos legales">
            <template
              v-for="docBlock in documents"
              :key="docBlock.id"
              #[docBlock.id]
            >
              <section>
                <h2 class="sr-only">{{ docBlock.title }}</h2>

                <section
                  v-for="(item, index) in docBlock.sections"
                  :id="`${docBlock.id}-${item.id}`"
                  :key="item.id"
                  class="mb-10 scroll-mt-24"
                >
                  <h3 class="text-lg font-semibold text-aqua-800 mb-3">
                    {{ index + 1 }}. {{ item.title }}
                  </h3>

                  <p
                    v-for="text in item.body"
                    :key="text"
                    class="text-slate-600 mb-3"
                  >
                    {{ text }}
                  </p>

                  <ul
                    v-if="item.list"
                    class="list-disc pl-5 text-slate-600 space-y-1 mb-3"
                  >
                    <li v-for="entry in item.list" :key="entry">{{ entry }}</li>
                  </ul>

                  <!-- Data table: scrolls inside its own box on narrow screens -->
                  <div v-if="item.rows" class="overflow-x-auto mb-3">
                    <table
                      class="w-full min-w-[36rem] text-sm text-left border border-slate-200 rounded-lg"
                    >
                      <thead class="bg-slate-50 text-slate-700">
                        <tr>
                          <th
                            v-for="header in item.rowHeaders ||
                            DEFAULT_ROW_HEADERS"
                            :key="header"
                            scope="col"
                            class="px-3 py-2 font-semibold"
                          >
                            {{ header }}
                          </th>
                        </tr>
                      </thead>
                      <tbody class="text-slate-600">
                        <tr
                          v-for="row in item.rows"
                          :key="row.data"
                          class="border-t border-slate-200 align-top"
                        >
                          <td class="px-3 py-2 font-medium text-slate-700">
                            {{ row.data }}
                          </td>
                          <td class="px-3 py-2">{{ row.purpose }}</td>
                          <td class="px-3 py-2">{{ row.time }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </section>
              </section>
            </template>
          </Tabs>
        </div>
      </div>

      <!-- Side index (desktop only), built from the same data as the content -->
      <aside class="hidden lg:block">
        <nav aria-label="Índice del documento" class="sticky top-24 text-sm">
          <!-- Both documents; a link to the other one switches tab (see the hash watcher) -->
          <template v-for="docBlock in documents" :key="docBlock.id">
            <p class="mb-2">
              <a
                :href="`#${docBlock.id}`"
                @click.prevent="goTo(`#${docBlock.id}`)"
                :aria-current="docBlock.id === activeTab ? 'true' : undefined"
                class="font-semibold hover:text-aqua-600"
                :class="
                  docBlock.id === activeTab ? 'text-aqua-900' : 'text-slate-600'
                "
              >
                {{ docBlock.title }}
              </a>
            </p>
            <ul class="space-y-1.5 text-slate-600 mb-5">
              <li v-for="(item, index) in docBlock.sections" :key="item.id">
                <a
                  :href="`#${docBlock.id}-${item.id}`"
                  class="hover:text-aqua-600"
                  @click.prevent="goTo(`#${docBlock.id}-${item.id}`)"
                >
                  {{ index + 1 }}. {{ item.short || item.title }}
                </a>
              </li>
            </ul>
          </template>
          <router-link
            to="/"
            class="font-semibold text-aqua-600 hover:text-aqua-900"
          >
            ← Volver al inicio
          </router-link>
        </nav>
      </aside>
    </div>
  </PublicLayout>
</template>

<script setup>
import { nextTick, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import PublicLayout from "../../layouts/PublicLayout.vue";
import Tabs from "../../components/Tabs.vue";

// Same value as TERMS_VERSION in the backend: it is saved with the user when they accept the terms
const LEGAL_VERSION = "2026-10";
const LAST_UPDATED = "octubre de 2026";

const summary = [
  "Solo damos servicio a edificios de Barcelona ciudad.",
  "La prueba gratuita dura 7 días. Al terminar, tus datos quedan en solo lectura hasta que te hagas cliente desde la plataforma.",
  "Al hacerte cliente eliges cuántos edificios y sensores necesitas: pagas la base del plan más 10 € por sensor al mes, por domiciliación SEPA.",
  "Los sensores los instala el equipo técnico de AquaGuard: necesitamos acceso al edificio.",
  "Guardamos solo lo necesario: tu cuenta, tus edificios, las lecturas de los sensores y los documentos que se suben.",
  "Una sola cookie, técnica y de sesión. Sin analítica ni publicidad. No vendemos ni cedemos datos.",
];

// Column titles of the data tables, unless a section sets its own rowHeaders
const DEFAULT_ROW_HEADERS = ["Dato", "Para qué", "Cuánto tiempo"];

// Each section: title, short (index label, optional), body (paragraphs), list and rows (optional)
const privacySections = [
  {
    id: "responsable",
    title: "Quiénes somos",
    short: "Titular",
    body: [
      "AquaGuard es un proyecto estrictamente académico, desarrollado por un equipo de estudiantes de 42 Barcelona para el currículo de 42 (ft_transcendence).",
      "No hay una sociedad detrás ni actividad comercial real, por eso no hay razón social, NIF ni domicilio social. Si el servicio pasara a ofrecerse de verdad, aquí aparecerían esos datos, como exigen la LSSI-CE (art. 10) y el RGPD (art. 13).",
      "Para cualquier cuestión sobre tus datos, escribe a soporte@aquaguard.dev.",
    ],
  },
  {
    id: "datos",
    title: "Qué datos tratamos y durante cuánto tiempo",
    short: "Datos y plazos",
    body: ["Solo los que hacen falta para que el servicio funcione:"],
    rows: [
      {
        data: "Nombre y email",
        purpose: "Identificarte y que puedas entrar",
        time: "Mientras tu cuenta exista",
      },
      {
        data: "Contraseña",
        purpose:
          "Comprobar que eres tú. Se guarda solo como hash Argon2, nunca en claro",
        time: "Mientras tu cuenta exista",
      },
      {
        data: "Organización y rol",
        purpose: "Decidir qué edificios, sensores y alertas puedes ver",
        time: "Mientras tu cuenta exista",
      },
      {
        data: "Aceptación de los términos",
        purpose: "Poder demostrar qué versión aceptaste y cuándo",
        time: "Mientras tu cuenta exista",
      },
      {
        data: "Datos de la organización, contrato y facturación",
        purpose:
          "Contactar con la organización y gestionar su contrato: plan, edificios y sensores contratados, precio, pago mensual o anual, razón social, NIF/CIF, dirección fiscal con código postal, email de facturación, email y teléfono de contacto, y cuándo autorizaste la domiciliación SEPA. Del IBAN solo guardamos el país y las 4 últimas cifras",
        time: "Mientras la organización tenga cuenta",
      },
      {
        data: "Edificios y sensores",
        purpose:
          "Dirección, distrito, plantas y ubicación de cada sensor, para mostrar el edificio planta a planta",
        time: "Mientras la organización tenga cuenta",
      },
      {
        data: "Lecturas y alertas",
        purpose:
          "Mostrar el estado de la red, generar alertas y saber quién las reconoció o resolvió",
        time: "Mientras la organización tenga cuenta",
      },
      {
        data: "Documentos",
        purpose: "Guardar los archivos de cada edificio (ver punto 5)",
        time: "Hasta que se borren o se elimine la organización",
      },
      {
        data: "Dirección IP",
        purpose: "Seguridad: registros del servidor",
        time: "El tiempo imprescindible para la seguridad",
      },
    ],
  },
  {
    id: "base",
    title: "Por qué podemos tratarlos",
    short: "Base legal",
    body: [
      "Porque son necesarios para prestar el servicio que tu organización ha solicitado, también durante la prueba gratuita (ejecución de un contrato, art. 6.1.b del RGPD). Los registros de seguridad se basan en nuestro interés legítimo en proteger la plataforma (art. 6.1.f del RGPD).",
    ],
  },
  {
    id: "quien",
    title: "Quién más los ve",
    short: "Quién los ve",
    body: [
      "Las personas de tu organización ven los datos de tu organización. El equipo de administración de AquaGuard ve los de todas, para dar soporte e instalar los sensores.",
      "No vendemos ni cedemos datos. Solo intervienen proveedores técnicos imprescindibles:",
    ],
    list: [
      "Alojamiento de la plataforma.",
      "Mapa: las teselas se cargan desde OpenFreeMap, que recibe tu dirección IP al mostrar el mapa.",
    ],
  },
  {
    id: "documentos",
    title: "Documentos",
    body: [
      "Cada edificio puede tener documentos asociados: informes de instalación, planos, fotos o exportaciones de lecturas. Se guardan los archivos (PDF, JPG, PNG o CSV de hasta 10 MB), su nombre, tipo, tamaño, el edificio al que pertenecen, quién los subió y cuándo.",
      "Los documentos de un edificio solo los ven las personas de su organización y el equipo de AquaGuard. Ninguna otra organización puede verlos.",
      "No subas documentos con datos personales que no sean necesarios para el servicio (por ejemplo, datos de vecinos o inquilinos).",
    ],
  },
  {
    id: "conservacion",
    title: "Qué pasa con los datos al terminar la prueba",
    short: "Fin de la prueba",
    body: [
      "Cuando terminan los 7 días de prueba, tus datos no se borran: quedan en solo lectura. Puedes seguir viendo tus edificios, lecturas y documentos, pero no hacer cambios.",
      "Si te haces cliente, todo sigue como estaba. Si no, el equipo de AquaGuard puede eliminar la organización; al hacerlo se borran de forma definitiva sus usuarios, edificios, sensores, lecturas, alertas y documentos.",
    ],
  },
  {
    id: "cookies",
    title: "Cookies",
    body: [
      "AquaGuard solo usa una cookie técnica de sesión, estrictamente necesaria para la autenticación y la seguridad. Las cookies de este tipo están exentas de consentimiento (art. 22.2 de la LSSI-CE), por eso no mostramos un aviso para aceptarlas.",
      "No usamos cookies de analítica, de publicidad ni de terceros.",
    ],
    rows: [
      {
        data: "aquaguard_session",
        purpose:
          "Mantener la sesión iniciada. Es propia, httpOnly (el navegador no la deja leer por JavaScript) y solo viaja por HTTPS",
        time: "8 horas, o hasta que cierres la sesión",
      },
    ],
    rowHeaders: ["Cookie", "Para qué", "Duración"],
  },
  {
    id: "derechos",
    title: "Tus derechos",
    body: [
      "Puedes pedir en cualquier momento acceder a tus datos, corregirlos, borrarlos, limitar su uso, oponerte a su tratamiento o llevártelos en un formato estándar.",
      "Desde Mi cuenta puedes descargar tus datos en un archivo JSON y pedir la baja: te enviamos un email de confirmación en los dos casos. Para el resto, escribe a soporte@aquaguard.dev.",
      "Si crees que no lo hemos hecho bien, puedes reclamar ante la Agencia Española de Protección de Datos (aepd.es).",
    ],
  },
  {
    id: "seguridad",
    title: "Cómo los protegemos",
    short: "Seguridad",
    body: [
      "Todo el tráfico va cifrado con HTTPS. Las contraseñas se guardan con hash. Cada usuario solo puede ver lo de su organización, y esto se comprueba en el servidor, no solo en la pantalla.",
      "Si hubiera una brecha de seguridad (un acceso indebido o una filtración de datos) que suponga un riesgo para las personas, la notificaremos a la Agencia Española de Protección de Datos en un plazo máximo de 72 horas desde que la conozcamos (art. 33 del RGPD). Si el riesgo es alto, también avisaremos sin demora a las personas afectadas (art. 34 del RGPD).",
    ],
  },
  {
    id: "menores",
    title: "Menores",
    body: [
      "AquaGuard es una herramienta profesional. No está pensada para menores de 14 años y no creamos cuentas para ellos.",
    ],
  },
  {
    id: "cambios",
    title: "Cambios en esta política",
    short: "Cambios",
    body: [
      "Si cambiamos algo importante, actualizaremos la versión y la fecha de esta página y te lo comunicaremos a través de la plataforma.",
    ],
  },
];

const termsSections = [
  {
    id: "quien-usa",
    title: "Quién puede usar AquaGuard",
    short: "Quién puede usarlo",
    body: [
      "Hay dos formas de tener cuenta: empezar la prueba gratuita de 7 días desde la web, o recibir una invitación de un administrador de AquaGuard que te asigna a tu organización. Al crear la cuenta aceptas estos términos y la política de privacidad.",
    ],
  },
  {
    id: "ambito",
    title: "Solo edificios de Barcelona",
    short: "Ámbito: Barcelona",
    body: [
      "AquaGuard solo da servicio a edificios situados en el término municipal de Barcelona. El equipo comprueba la dirección del edificio antes de instalar los sensores: si está fuera de Barcelona, no podremos instalarlos ni darte de alta como cliente.",
    ],
  },
  {
    id: "prueba",
    title: "Prueba gratuita de 7 días",
    short: "Prueba gratuita",
    body: [
      "La prueba es gratuita, no pide tarjeta y no te compromete a nada. Dura 7 días desde el registro. Durante la prueba tu organización puede tener un edificio.",
      "Al terminar, la cuenta queda en solo lectura: puedes ver tus edificios, lecturas y documentos, pero no hacer cambios. Para seguir usando AquaGuard, hazte cliente desde la plataforma (en el aviso de la prueba o en Mi cuenta). El equipo también puede ampliar la prueba.",
      "Si no te haces cliente, el equipo puede eliminar la organización y todos sus datos, como explica la política de privacidad.",
    ],
  },
  {
    id: "contratacion",
    title: "Contratación, precio y pago",
    short: "Contratación y pago",
    body: [
      "Al hacerte cliente eliges cuántos edificios y sensores necesitas, y el plan se elige solo según los edificios: Básico (de 1 a 5), Profesional (de 6 a 10) o Empresa (de 11 a 20). Los sensores no cambian el plan, se pagan aparte. Para más de 20 edificios, escríbenos y te preparamos un presupuesto.",
      "El precio al mes es la base del plan (29 €, 79 € o 199 €) más 10 € por cada sensor, IVA no incluido. Puedes pagar cada mes, sin permanencia, o un año por adelantado, que son 10 meses. El precio queda fijado el día del alta y el servicio de pago empieza ese mismo día.",
      "Lo contratado es también tu máximo: no damos de alta más edificios ni sensores de los que pagas, y no puedes contratar menos de los que ya tienes. Para ampliar el contrato, escríbenos.",
      "El cobro es por domiciliación SEPA en la cuenta que indicas al contratar, que tiene que ser un IBAN español, y para eso nos autorizas en el mismo formulario. Al contratar aceptas también estas condiciones.",
      "AquaGuard es un proyecto académico: el alta funciona como una real, pero no se hace ningún cobro.",
    ],
  },
  {
    id: "instalacion",
    title: "Instalación de los sensores",
    short: "Instalación",
    body: [
      "Los sensores los instala el equipo técnico de AquaGuard. Para hacerlo, tu organización se compromete a:",
    ],
    list: [
      "Dar acceso al edificio en la fecha acordada: zonas comunes, cuartos de contadores y plantas donde vayan los sensores.",
      "Tener los permisos necesarios (por ejemplo, de la comunidad de propietarios o de la propiedad del edificio).",
      "No mover, desconectar ni manipular los sensores. Si hay que cambiarlos de sitio, avísanos.",
    ],
  },
  {
    id: "cuenta",
    title: "Tu cuenta",
    body: [
      "Es personal. No compartas tu contraseña. Si crees que alguien ha entrado con ella, cámbiala desde Mi cuenta y avísanos.",
    ],
  },
  {
    id: "uso",
    title: "Uso aceptable",
    body: [
      "No intentes acceder a datos de otras organizaciones, saturar el servicio ni alterar las lecturas de los sensores.",
    ],
  },
  {
    id: "documentos",
    title: "Documentos",
    body: [
      "Puedes subir documentos de tus edificios (PDF, JPG, PNG o CSV de hasta 10 MB). Eres responsable de lo que subes y de tener derecho a compartirlo.",
      "Puedes borrar los documentos que sube tu organización. Los que sube el equipo de AquaGuard (por ejemplo, el informe de instalación) solo los puede borrar el equipo.",
    ],
  },
  {
    id: "alertas",
    title: "Las alertas no sustituyen a un sistema de emergencia",
    short: "Alertas",
    body: [
      "AquaGuard te avisa cuando una lectura sale de rango o un sensor deja de enviar datos, pero una alerta puede llegar tarde o no llegar (por ejemplo, si cae la conexión). Ante una fuga real, actúa según tus protocolos y avisa a los servicios de emergencia si hace falta.",
    ],
  },
  {
    id: "disponibilidad",
    title: "Disponibilidad",
    body: [
      "Es un proyecto académico. Intentamos que funcione siempre, pero no garantizamos un tiempo mínimo de servicio. Puede haber mantenimientos o interrupciones puntuales.",
    ],
  },
  {
    id: "datos-org",
    title: "Los datos de tu organización",
    short: "Datos de tu organización",
    body: [
      "Las lecturas, alertas y documentos son de tu organización. Nosotros solo los usamos para prestarte el servicio, como explica la política de privacidad.",
    ],
  },
  {
    id: "baja",
    title: "Darse de baja",
    short: "Baja",
    body: [
      "Puedes pedir la baja en cualquier momento desde Mi cuenta. Un administrador revisa la petición y cierra la cuenta; con la baja termina también tu contrato. Un administrador también puede suspender o eliminar una cuenta si se incumplen estos términos.",
    ],
  },
  {
    id: "cambios",
    title: "Cambios en estos términos",
    short: "Cambios",
    body: [
      "Si cambian de forma importante, actualizaremos la versión y la fecha de esta página y te lo comunicaremos a través de la plataforma.",
    ],
  },
  {
    id: "ley",
    title: "Ley aplicable y tribunales",
    short: "Ley y tribunales",
    body: [
      "Estos términos se rigen por la legislación española.",
      "Las partes se someten a los Juzgados y Tribunales de la ciudad de Barcelona, salvo que la ley atribuya la competencia a otro fuero de forma imperativa, como ocurre cuando el cliente actúa como consumidor.",
    ],
  },
];

const documents = [
  {
    id: "privacidad",
    title: "Política de privacidad",
    sections: privacySections,
  },
  { id: "terminos", title: "Términos de servicio", sections: termsSections },
];

const TABS = documents.map((docBlock) => ({
  key: docBlock.id,
  label: docBlock.title,
}));

const route = useRoute();
const router = useRouter();

// The tab comes from the URL hash: #terminos or #terminos-<section> opens the terms
function tabFromHash(hash) {
  return hash.startsWith("#terminos") ? "terminos" : "privacidad";
}

const activeTab = ref(tabFromHash(route.hash));

// Scrolls to the element of the hash, leaving room for the sticky header.
// The router does not scroll on this page (meta.handlesHashScroll), because the
// target may be in the other tab, which is not rendered yet.
function scrollToHash(hash) {
  const target = hash && document.getElementById(hash.slice(1));
  if (!target) return;

  const header = document.querySelector("header");
  const offset = (header?.offsetHeight ?? 0) + 16;
  const top = target.getBoundingClientRect().top + window.scrollY - offset;

  window.scrollTo({ top: Math.max(0, top) });
}

// Waits until the tab is rendered and painted, then scrolls
async function scrollAfterRender(hash) {
  await nextTick();
  requestAnimationFrame(() => scrollToHash(hash));
}

// Side index links: same hash again still scrolls (the watcher only sees changes)
function goTo(hash) {
  if (route.hash === hash) {
    scrollAfterRender(hash);
  } else {
    router.push({ hash });
  }
}

// Any hash change on this page (side index, footer links): switch tab, then scroll
watch(
  () => route.hash,
  (hash) => {
    if (!hash) return;
    activeTab.value = tabFromHash(hash);
    scrollAfterRender(hash);
  },
);

// Opening /legal#... from another page
onMounted(() => scrollAfterRender(route.hash));

// Clicking a tab updates the hash, so the URL can be shared and the back button works
watch(activeTab, (tab) => {
  if (tabFromHash(route.hash) !== tab) router.replace({ hash: `#${tab}` });
});
</script>
