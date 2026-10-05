# Issue 07 — Verificación

Probado en `/admin` con el `mockAdapter` modificado temporalmente (retraso de 2 s y errores forzados; cambio no incluido en la PR).

| Caso | Resultado esperado | OK |
|---|---|---|
| Carga | Spinner compacto en cada tarjeta; KPIs en `—` | ✅ |
| Error | `ErrorState` con mensaje del store; KPIs en `—` | ✅ |
| Retry | Repite la action del store; cada tarjeta se recupera de forma independiente | ✅ |
| Vacío | `EmptyState`; KPIs en `0` | ✅ |
| Éxito | Listas y KPIs con datos; el mapa refleja las alertas | ✅ |
| Foco | Sin foco automático al cargar; tras retry fallido, foco en "Reintentar" | ✅ |
| Consola | Sin `Uncaught (in promise)` | ✅ |
| Build | `npm run build` sin errores | ✅ |

Pendiente fuera de este issue: el repo no tiene configuración de ESLint (`npm run lint` falla también en `develop`).
