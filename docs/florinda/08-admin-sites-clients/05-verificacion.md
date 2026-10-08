# Verificación — Issue 08

| Prueba | Resultado |
|---|---|
| `/admin/clients` muestra los clientes con su nº de sites | ✅ |
| Loading, error y vacío se renderizan cambiando las props | ✅ |
| Detalle de un cliente con sites y de uno sin sites | ✅ |
| Ruta directa con id inválido → "Cliente no encontrado" | ✅ |
| `/admin/sites`: hover visible y clic abre el cliente | ✅ |
| "← Volver a clientes" y botón atrás del navegador | ✅ |
| Sidebar: apartado activo correcto, también en el detalle | ✅ |
| Sensores/Alertas atenuados con "Próximamente" | ✅ |
| Móvil: el menú se cierra al pulsar un enlace | ✅ |
| Dashboard sin cambios (sites no clicables) | ✅ |
| `ClientsList` y `SitesSummary` sin stores ni HTTP | ✅ |
| Consola sin avisos nuevos | ✅ |

Pendiente para #10: `favicon.ico` 404; en 360 px el botón ☰ se superpone al título del Header.