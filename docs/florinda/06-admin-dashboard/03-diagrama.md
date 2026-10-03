# Diagrama — Issue 06 (Dashboard Admin)

```mermaid
flowchart TD
 A[Antes: Admin sin vista operativa] --> B[Información dispersa]

 classDef default fill:#e0f2fe,stroke:#0369a1,color:#0f172a
```

```mermaid
flowchart LR
 A[AdminLayout] --> B[DashboardView]
 B --> C[KPIs]
 B --> D[Resumen Sites]
 B --> E[Resumen Sensors]
 B --> F[Resumen Alerts]
 G["Stores y Services del frontend"] -. props .-> B

 classDef default fill:#e0f2fe,stroke:#0369a1,color:#0f172a
```

## Estados de una sección

```mermaid
stateDiagram-v2
 [*] --> Loading
 Loading --> Ready
 Loading --> Empty
 Loading --> Error
 Ready --> Loading: refresh
 Error --> Loading: retry

 classDef estado fill:#e0f2fe,stroke:#0369a1,color:#0f172a
 class Loading, Ready, Empty, Error estado
```

## Flujo de datos implementado

Regla general: **los datos bajan, nunca se piden**. Los stores de Pinia guardan los datos, la vista los prepara y los componentes solo los pintan.

```mermaid
flowchart LR
 subgraph ENTRA["1. Entra: stores de Pinia"]
  S1["sensorStore.sensorCount"]
  S2["sensorStore.sensors"]
  S3["alertsStore.alerts"]
  S4["sites: sin store todavía"]
 end

 subgraph TRANSFORMA["2. Se transforma: computed en DashboardView.vue"]
  C1["totalSensors"]
  C2["onlineSensors: filter ONLINE, length"]
  C3["activeAlertList: filter ACTIVE"]
  C4["activeAlerts: activeAlertList.length"]
 end

 subgraph SALE["3. Sale: props a componentes presentacionales"]
  K1["KPICard Sensores totales"]
  K2["KPICard Sensores online"]
  K3["KPICard Alertas activas"]
  K4["KPICard Sites: valor por defecto"]
  L1["SensorsSummary :sensors"]
  L2["AlertsSummary :alerts"]
  L3["SitesSummary: lista vacía por defecto"]
 end

 S1 --> C1 --> K1
 S2 --> C2 --> K2
 S2 -- "lista tal cual" --> L1
 S3 --> C3 --> C4 --> K3
 C3 --> L2
 S4 -. "sin datos" .-> K4
 S4 -. "sin datos" .-> L3

 classDef default fill:#e0f2fe,stroke:#0369a1,color:#0f172a
 style ENTRA fill:#f8fafc,stroke:#94a3b8,color:#0f172a
 style TRANSFORMA fill:#f8fafc,stroke:#94a3b8,color:#0f172a
 style SALE fill:#f8fafc,stroke:#94a3b8,color:#0f172a
```

| Fase | Qué es | Ejemplo |
|---|---|---|
| **Entra** | Listas del store, con el shape del backend | `[{ id, name, status: 'ONLINE', ... }]` |
| **Se transforma** | `computed`: filtra o cuenta, y se recalcula solo cuando cambia el store | `alertsStore.alerts.filter(a => a.status === 'ACTIVE')` |
| **Sale** | Props hacia componentes que solo pintan | `<AlertsSummary :alerts="activeAlertList" />` |

## Cómo se compone la página

```mermaid
flowchart TD
 R["Router /admin"] --> V["DashboardView.vue"]
 V --> L["AdminLayout.vue"]
 L --> H["Header: prop title, slot #actions"]
 L --> SB["Sidebar: prop appName"]
 L --> M["main: slot por defecto"]
 L --> FT["Footer"]
 M --> KP["4 x KPICard: props label, value y slot #icon"]
 M --> SS["SitesSummary: prop sites"]
 M --> SN["SensorsSummary: prop sensors"]
 M --> AS["AlertsSummary: prop alerts"]
 KP --> AI["AppIcon: prop name"]
 SB --> AI
 SS --> AI
 SN --> AI
 AS --> AI

 classDef default fill:#e0f2fe,stroke:#0369a1,color:#0f172a
```

## Dentro de cada resumen

Los tres resúmenes siguen el mismo patrón:

```mermaid
flowchart LR
 P["prop: lista (por defecto vacía)"] --> Q{"¿lista.length === 0?"}
 Q -- sí --> E1["Mensaje de estado vacío"]
 Q -- no --> E2["v-for: un li por elemento, con :key = id"]
 E2 --> B["Etiqueta de estado con :class condicional"]

 classDef default fill:#e0f2fe,stroke:#0369a1,color:#0f172a
```

| Componente | Recibe | Etiqueta |
|---|---|---|
| `SitesSummary` | `sites` | — (nombre y dirección) |
| `SensorsSummary` | `sensors` | `ONLINE` verde / `OFFLINE` gris |
| `AlertsSummary` | `alerts` (solo `ACTIVE`) | `CRITICAL` rojo / `WARNING` ámbar |

## Qué NO hace ningún componente

- No importa `axios` ni llama a `/api/...` (criterio: sin HTTP directo).
- No llama a `fetchSensors()` ni a otras acciones de carga: la carga de datos en los stores pertenece a los issues de integración de stores y services ("Integrar Sensors y Readings con Services/Stores", #34, y "Implementar sensores, alertas, tablas y filtros de Admin").
- No reconoce ni resuelve alertas: la gestión funcional de alertas pertenece al issue "Implementar sensores, alertas, tablas y filtros de Admin" (frontend) y al #28 (endpoints de alertas, backend).
- No decide de dónde vienen los datos: si mañana llegan de la API real, los componentes no cambian.
