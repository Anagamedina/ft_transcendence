# Implementación — Issue 08

## Rutas

| Ruta | Vista | Contenido |
|---|---|---|
| `/admin/clients` | `ClientsView` | Listado de clientes (organizaciones) |
| `/admin/clients/:id` | `ClientDetailView` | Datos del cliente y sus sites; "no encontrado" si el id no existe |
| `/admin/sites` | `SitesView` | Listado de sites; al pulsar uno se abre su cliente |

## Componentes

- **`ClientsList`** (nuevo): presentacional. Usa `Card` y los estados Loading/Error/Empty (#37).
- **`SitesSummary`** (reutilizado): nueva prop opcional `selectable`. Sin ella, el Dashboard no cambia.
- **`Sidebar`**: los enlaces llegan por la prop `items` y se pintan con `router-link`. Marca el apartado activo (también en rutas hijas) y muestra atenuados los que aún no tienen ruta. Sin `items` mantiene el menú original.
- **`AppIcon`**: nuevo icono `users`.

## Contrato para el área de datos

| Componente | Props | Eventos |
|---|---|---|
| `ClientsList` | `clients` `[{ id, name, created_at, sites_count? }]`, `loading`, `error`, `search` | `select(client)`, `retry`, `update:search` |
| `SitesSummary` | `sites` (shape `SiteResponse`), `selectable` | `select(site)` |

## Datos temporales

- Clientes: `views/admin/mockClients.js` (shape `OrganizationResponse`).
- Sites: `services/fixtures/sites.js`.
- Ambos marcados con `TODO`; se sustituyen por el store cuando exista.

## Fuera de alcance

Filtros funcionales, paginación, estado global y llamadas a la API (área de datos). Alta de organizaciones y ruta protegida: #122.
