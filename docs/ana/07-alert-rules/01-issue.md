# Issue 07 — Reglas y endpoints básicos de alertas

## 1. Objetivo

Evaluar lecturas para detectar presión baja/alta y sensores offline cuando aplique, y exponer alertas para consulta, reconocimiento y resolución.

## 2. Separación de responsabilidades

Daruny persiste `Alert`; Ana decide cuándo crearla y qué significa cada estado. El simulador genera escenarios, pero no crea alertas directamente.

## 3. Dependencias y límites

Depende de modelo/repository Alert, readings y simulador de Daruny, schemas, auth y permisos. No incluye persistencia, queries SQLAlchemy ni Docker.

## 4. Aprendizaje estimado

Reglas/umbrales — 45 min; máquina de estados — 45 min; idempotencia — 45 min; endpoints y pruebas — 90 min.

## 5. Finalidad

Convierte datos en información accionable para el dashboard. Las alertas se generan sin duplicación descontrolada y pueden consultarse, reconocerse y resolverse.

## 6. Criterios de aceptación

- [ ] LOW/HIGH se evalúan con umbrales acordados.
- [ ] OFFLINE tiene definición temporal clara.
- [ ] Alertas respetan estados y severidad.
- [ ] GET filtra por organización/estado según contrato.
- [ ] Acknowledge/resolve son seguros e idempotentes.
