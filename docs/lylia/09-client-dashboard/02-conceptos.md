# Conceptos — Issue 09

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Client scope | Datos limitados a organización | 30 min |
| Protected route | Acceso condicionado por guard | 20 min |
| Dashboard composition | Resúmenes y detalle en una vista | 25 min |
| Shared component | Reutilización sin duplicar UI | 20 min |
| Partial failure | Un bloque falla y otros siguen | 25 min |
| Privacy by design | No cargar ni mostrar datos ajenos | 25 min |

## Conceptos en conjunto

Guard mejora navegación; backend garantiza tenant; stores coordinan datos; componentes presentan. El dashboard no debe confiar en un `organization_id` enviado desde la URL.

## Errores frecuentes

Reutilizar store Admin sin scope, ocultar datos solo con CSS, cargar todo antes de renderizar y tratar un error de alertas como error de toda la página.

## Qué debes dominar antes de implementar

- Seguir el tenant desde Auth Store hasta la API.
- Separar error parcial de error global.
- Limpiar datos privados al cambiar de usuario.
- Probar dos organizaciones con datos distintos.

## Qué debes poder demostrar

- Explicar cómo se mantiene el scope del cliente.
- Distinguir error parcial de error global.
- Probar un usuario con datos y otro sin datos.
