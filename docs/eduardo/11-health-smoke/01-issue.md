# Issue 11 — Health checks y smoke test

## 1. Objetivo

Detectar fallos básicos de infraestructura y demostrar el flujo mínimo `simulator → API → database` antes de mergear o evaluar. La comprobación debe fallar de forma visible cuando una dependencia no está disponible.

La pregunta central es: ¿cómo sabemos, con una ejecución corta, que los servicios están vivos, listos y conectados entre sí?

## 2. Qué se comprueba

1. PostgreSQL está listo para aceptar conexiones.
2. Backend está arrancado y puede responder.
3. Simulator puede enviar una lectura.
4. API responde con éxito.
5. La lectura llega a la persistencia.

## 3. Requisitos y límites

Health de backend y database, estado de Compose, smoke test automatizable y documentación. No incluye tests unitarios de services/endpoints.

## 4. Diferencia importante

Liveness responde “¿el proceso vive?”. Readiness responde “¿puede recibir trabajo?”. Un contenedor `running` puede estar vivo pero no listo porque aún espera PostgreSQL.

## 5. Dependencias

Depende de Compose, del health de backend/database, del simulator y del contrato de readings. El smoke test no sustituye los tests unitarios de Ana.

## 6. Aprendizaje estimado

Health/readiness — 30 min; smoke testing HTTP — 45 min; diagnóstico Docker — 30 min; implementación — 60–90 min.

## 7. Finalidad para el proyecto

Proporciona una barrera rápida contra errores de configuración, DNS, variables, orden de arranque o integración. Es especialmente útil antes de una demo o merge.

## 8. Criterios de aceptación

- [ ] Database reporta readiness.
- [ ] Backend reporta readiness según sus dependencias.
- [ ] Compose muestra estados saludables.
- [ ] El smoke test espera readiness con timeout.
- [ ] Una lectura válida devuelve respuesta exitosa.
- [ ] Se comprueba su persistencia.
- [ ] Cualquier fallo termina con código distinto de cero y diagnóstico.
