# Implementación — Issue 04

## Fase 1 — Mensaje

1. Definir audiencia y propuesta de valor.
2. Ordenar hero, beneficios, CTA y footer.
3. Evitar texto técnico innecesario.

## Fase 2 — Construcción

1. Crear vista en ruta pública.
2. Integrar Header/Footer.
3. Añadir enlaces Router a login/registro.
4. Usar semántica HTML y assets optimizados.

## Fase 3 — Verificación

1. Navegar sin sesión.
2. Probar cada CTA y refresh directo de ruta.
3. Revisar móvil/desktop, teclado, contraste y consola.

## Criterio de entrega

Solicitar revisión del mensaje y no solo del CSS. La página está terminada cuando alguien que no conoce el código entiende el producto y encuentra la siguiente acción sin ayuda.

## Notas de implementación adicionales

### Copy de la Landing: audiencia general, no B2B/B2G puro
Un análisis externo sugería reposicionar el copy hacia un público exclusivamente empresarial/institucional. Se descartó porque el subject del Issue #5 especifica audiencia general (particulares + empresas), y cambiar el enfoque habría requerido reabrir el issue con el Product Owner.

### Navegador de evaluación exigido: Chrome — pruebas reales en Chrome y Firefox
El subject (§2, tabla de requisitos Mandatory) solo exige "compatible con la última versión estable de Chrome" y "prueba final en Chrome"; no hay requisito de Firefox u otros navegadores en ningún punto del documento. Aun así, las pruebas de responsive y accesibilidad de este issue se hicieron en **ambos navegadores, Chrome y Firefox**, como verificación adicional más allá del mínimo exigido. La entrega final debe validarse en Chrome (criterio de evaluación), pero el comportamiento ya está confirmado también en Firefox.

### Iconografía: SVG propios en vez de emojis o librería externa
Se sustituyeron los emojis usados en mockups iniciales por 4 iconos SVG dibujados a mano (rayo, gráfico de barras, campana, gráfico ascendente), marcados `aria-hidden="true"` porque son decorativos y el texto adyacente ya los describe. Se evitó añadir una librería de iconos para no incrementar el bundle sin necesidad, dado que solo se usan 4 iconos.

### SVG decorativos y bloqueo de clics (`pointer-events-none`)
El SVG de la onda divisoria del Hero, al estar `position: absolute`, ocupa su rectángulo completo (`viewBox`) para efectos de clic, incluidas las zonas transparentes — no solo donde pinta color. Al venir después en el DOM y estar posicionado, quedaba por encima del CTA "Comenzar ahora" en el orden de apilado, bloqueando el clic aunque visualmente no lo tapara. Se añadió `pointer-events-none` al SVG. **Cualquier elemento decorativo posicionado en absoluto sobre contenido interactivo debe llevar `pointer-events-none`**, aunque a simple vista no parezca solaparse.
