# Documentación de issues de Daruny

Esta documentación sigue las issues definidas en [`scripts/create_daruny_issues.sh`](../../scripts/create_daruny_issues.sh). Cada carpeta contiene cuatro documentos:

1. `01-issue.md`: alcance, propósito, requisitos, aprendizaje estimado y criterios de aceptación.
2. `02-conceptos.md`: conceptos técnicos necesarios, orden recomendado y tiempo de estudio.
3. `03-diagrama.md`: comparación visual del antes y el después mediante Mermaid.
4. `04-implementacion.md`: pasos concretos, ordenados y verificables.

## Orden recomendado

```mermaid
flowchart LR
 I01[01 PostgreSQL + SQLAlchemy] --> I02[02 Alembic]
 I02 --> I03[03 Modelos y relaciones]
 I03 --> I04[04 Repositories Sensors/Readings]
 I03 --> I05[05 Seed]
 I04 --> I06[06 Simulador]
 I03 --> I07[07 Repositories Users/Organizations]
 I03 --> I08[08 Repository Alerts]
 I04 --> I09[09 Docker Compose]
 I09 --> I10[10 Nginx + HTTPS]
 I09 --> I11[11 Health checks + smoke test]
```

Las issues 04 y 05 desbloquean el vertical slice; la 06 depende además de que Ana exponga `POST /api/readings`. Las issues 09–11 son de infraestructura y se pueden preparar parcialmente mientras avanza el backend.

