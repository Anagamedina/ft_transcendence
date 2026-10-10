# Issue 03 — SensorCard y detalle visual de sensor

## 1. Objetivo

Crear la representación visual reutilizable de un sensor y una vista de detalle básica, preparada para recibir datos desde mocks o API sin conocer su origen.

## 2. Datos y estados

Debe mostrar nombre, ubicación, estado y valor principal. Los estados visuales serán normal, warning y critical, con diferencias comprensibles y no basadas solo en color.

## 3. Dependencias y límites

Depende de layouts/componentes compartidos. User04 proporcionará shape de datos e integración con services/stores. No incluye Axios, HTTP, estado global ni llamadas desde el componente.

## 4. Aprendizaje estimado

Props y composición — 30 min; estados visuales — 30 min; responsive/card design — 30 min; accesibilidad — 30 min; implementación/pruebas — 60 min.

## 5. Finalidad

Es el primer componente del vertical slice: traduce un objeto sensor en una UI clara y reutilizable.

## 6. Criterios de aceptación

- [ ] SensorCard funciona solo con props.
- [ ] Muestra los campos acordados.
- [ ] Normal/warning/critical son distinguibles.
- [ ] No realiza HTTP ni importa stores.
- [ ] Detalle navega y muestra un estado vacío/error definido.

## 6. Decisiones técnicas

- La tarjeta recibe un objeto ya preparado y no calcula umbrales.
- Estado visual debe incluir texto/icono además de color.
- Valor y unidad deben presentarse juntos.
- Datos faltantes tienen una representación explícita.

## 7. Casos que deben contemplarse

- Sensor normal, warning, critical y offline.
- Nombre largo y ubicación extensa.
- Valor sin lectura disponible.
- Lista vacía y error en detalle.
