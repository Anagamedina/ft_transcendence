# Implementación — Issue 03

## Fase 1 — Contrato

1. Acordar con User04 nombres, tipos, unidades y estados.
2. Separar datos obligatorios de opcionales.
3. Definir cómo se representa loading/error/empty en la vista de detalle.

## Fase 2 — UI

1. Implementar SensorCard con props.
2. Crear mapper visual de estados con texto, icono y color/contraste.
3. Crear detalle usando layout compartido.
4. Mantener HTTP/store fuera del componente.

## Fase 3 — Verificación

1. Renderizar normal, warning, critical y datos incompletos.
2. Probar teclado, contraste y viewport móvil.
3. Montar con mock y confirmar que el mismo shape sirve para API.

## Errores frecuentes

Hardcodear valores, usar solo colores, llamar Axios desde Card y acoplar el componente a un store concreto.

## Criterio de entrega

Documentar el shape de props y los estados soportados para que User04 pueda conectar la tarjeta sin reinterpretar el componente.
