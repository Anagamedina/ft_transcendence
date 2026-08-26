# Documentación de issues de Ana

Esta documentación corresponde a las 9 issues definidas en [`scripts/create_ana_issues.sh`](../../scripts/create_ana_issues.sh). Cada carpeta contiene:

- `01-issue.md`: contexto, objetivo, límites, dependencias y aceptación.
- `02-conceptos.md`: conceptos aislados y relacionados, con tiempo de aprendizaje.
- `03-diagrama.md`: flujo antes/después en Mermaid.
- `04-implementacion.md`: implementación por fases, pruebas y errores frecuentes.

## Orden recomendado

```mermaid
flowchart LR
 I01[01 FastAPI + módulos] --> I02[02 Schemas + OpenAPI]
 I02 --> I03[03 POST readings]
 I02 --> I04[04 GET sensors/history]
 I01 --> I05[05 Auth]
 I05 --> I06[06 Permisos y tenant]
 I02 --> I07[07 Alertas]
 I06 --> I07
 I06 --> I08[08 Sites y Sensors]
 I03 --> I09[09 Tests críticos]
 I04 --> I09
 I05 --> I09
 I06 --> I09
 I07 --> I09
```

Las issues 03, 04, 07 y 08 dependen de modelos/repositories de Daruny. La issue 09 se construye progresivamente conforme existan rutas y reglas que probar.
