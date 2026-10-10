# Issue 09 — Dashboard Client

## 1. Objetivo

Construir el área privada del cliente mostrando únicamente sensores, alertas, histórico y perfil de su organización.

## 2. Flujo esperado

```text
Client route → guard → Client Store/Services → API con tenant → componentes compartidos
```

## 3. Dependencias y límites

Depende de layouts/componentes de Florinda, auth/guards, endpoints y permisos backend. No rediseña Header, Sidebar, Cards ni sistema visual.

## 4. Aprendizaje estimado

Composición de dashboard — 45 min; tenant/auth — 30 min; estado remoto — 30 min; integración — 60 min; pruebas de seguridad UX — 90 min.

## 5. Finalidad

Client obtiene una vista útil sin ver datos ajenos y reutilizando el sistema visual existente.

## 6. Criterios de aceptación

- [ ] Ruta Client protegida.
- [ ] Solo muestra datos de su organización.
- [ ] Sensores, alertas e histórico se integran.
- [ ] Loading/Error/Empty presentes.
- [ ] Navegación Client funcional.
- [ ] Componentes compartidos reutilizados.

## 6. Casos límite

Organización sin datos, auth expirada, 403, error parcial, sensor sin readings y usuario con perfil incompleto.

## 7. Decisiones técnicas

- Cada bloque puede cargar de forma independiente.
- El tenant procede de auth/backend, no de un ID editable en la URL.
- Un error parcial debe comunicar qué sección falló.
- Reutilizar componentes de Florinda, sin copiar estructura global.

## 8. Resultado para el proyecto

Client obtiene una vista privada que demuestra aislamiento, consumo de datos y experiencia completa del MVP.
