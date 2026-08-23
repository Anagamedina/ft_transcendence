## Objetivo final de la tarea

Al terminar esta issue debes poder demostrar este flujo:

```text
FastAPI
  ↓
SQLAlchemy Session
  ↓
SQLAlchemy Engine
  ↓
PostgreSQL Driver
  ↓
PostgreSQL
```

Y además cumplir estos criterios:

* [ ] PostgreSQL funciona.
* [ ] FastAPI puede conectarse a PostgreSQL.
* [ ] SQLAlchemy gestiona sesiones correctamente.
* [ ] Existe una estrategia básica de `commit / rollback / close`.
* [ ] Las credenciales reales no están versionadas.
* [ ] La configuración funciona desde Docker.

Según el documento del proyecto, esto encaja directamente con tu responsabilidad de Backend Data & Infrastructure: PostgreSQL, SQLAlchemy, sesiones/transacciones, variables de entorno y Docker.

---

# Área 0 — Preparación y comprensión

**Tiempo estimado: 30–45 min**

Antes de tocar código, asegúrate de poder explicar estos conceptos:

* [ ] Qué es PostgreSQL.
* [ ] Qué es un driver PostgreSQL.
* [ ] Qué hace SQLAlchemy.
* [ ] Diferencia entre `Engine` y `Session`.
* [ ] Qué significa `commit`.
* [ ] Qué significa `rollback`.
* [ ] Qué significa `close`.
* [ ] Qué es una variable de entorno.
* [ ] Por qué `.env` no debe subirse a Git.
* [ ] Qué es una red de Docker Compose.

Tu modelo mental debe ser:

```text
Session = unidad de trabajo
Engine  = administra conexiones
Driver  = permite a Python hablar con PostgreSQL
PostgreSQL = almacena realmente los datos
```

No avances hasta que estas cuatro piezas estén claras.

---

# Área 1 — Revisar la estructura actual del backend

**Tiempo estimado: 15–30 min**

Primero inspecciona qué existe ya en vuestro repositorio.

Debes localizar:

```text
aquaguard/
├── compose.yaml
├── .gitignore
├── .env.example
│
└── backend/
    └── app/
        ├── main.py
        └── core/
```

Según la arquitectura propuesta en el documento, dentro de `core/` deberían terminar existiendo:

```text
backend/app/core/
├── config.py
└── database.py
```

### Antes de modificar nada

* [ ] Actualizar tu rama desde `develop`.
* [ ] Crear una rama específica de esta issue.
* [ ] Comprobar qué archivos existen ya.
* [ ] No sobrescribir configuración hecha por otros compañeros sin revisarla.

Resultado esperado:

```text
Sé dónde colocar cada parte de mi implementación.
```

---

# Área 2 — PostgreSQL en Docker

**Tiempo estimado: 45–60 min**

Tu primer objetivo técnico debe ser:

```text
Docker
   ↓
PostgreSQL funcionando
```

Todavía no conectes FastAPI.

## Paso 2.1 — Crear/configurar servicio `database`

En `compose.yaml` necesitarás conceptualmente:

```text
database
├── imagen PostgreSQL
├── usuario
├── contraseña
├── nombre DB
├── volumen persistente
└── healthcheck
```

El documento indica específicamente:

* PostgreSQL como DB.
* puerto interno `5432`.
* volumen persistente.
* healthcheck mínimo para database.

## Paso 2.2 — Variables

Prepara:

```text
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
```

No pongas valores sensibles directamente en el Compose.

## Paso 2.3 — Persistencia

Configura un volumen:

```text
postgres_data
```

Objetivo:

```text
eliminar/recrear contenedor
        ↓
los datos siguen existiendo
```

## Paso 2.4 — Levantar solo PostgreSQL

Primero prueba únicamente:

```bash
docker compose up database
```

o en background:

```bash
docker compose up -d database
```

## Paso 2.5 — Comprobar estado

Debes poder comprobar que PostgreSQL:

* [ ] arrancó.
* [ ] no entra en restart loop.
* [ ] pasa el healthcheck.
* [ ] acepta conexiones.

### Fin de esta área

No sigas hasta poder afirmar:

```text
PostgreSQL funciona de forma independiente.
```

---

# Área 3 — Variables de entorno y secretos

**Tiempo estimado: 30 min**

Ahora separa configuración de código.

Debes tener:

```text
.env
.env.example
.gitignore
```

## `.env`

Contiene valores reales de desarrollo:

```text
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
POSTGRES_HOST
POSTGRES_PORT
```

Este archivo:

```text
❌ NO Git
```

## `.env.example`

Contiene únicamente ejemplos seguros:

```text
POSTGRES_USER=aquaguard
POSTGRES_PASSWORD=change_me
POSTGRES_DB=aquaguard
POSTGRES_HOST=database
POSTGRES_PORT=5432
```

Este archivo:

```text
✅ SÍ Git
```

## `.gitignore`

Debe contener al menos:

```text
.env
```

### Comprobación obligatoria

Ejecuta:

```bash
git status
```

Asegúrate de que `.env` no aparece como archivo que vas a subir.

Este punto forma parte directamente de los criterios de aceptación de tu issue.

---

# Área 4 — Dependencias Python

**Tiempo estimado: 20–30 min**

Ahora prepara el backend para poder hablar con PostgreSQL.

Necesitarás como conceptos:

```text
FastAPI
SQLAlchemy
PostgreSQL driver
```

El flujo será:

```text
Python
 ↓
SQLAlchemy
 ↓
driver
 ↓
PostgreSQL
```

En esta fase solo debes conseguir:

* [ ] SQLAlchemy instalado.
* [ ] driver PostgreSQL instalado.
* [ ] imports funcionando.
* [ ] dependencias registradas en el archivo correspondiente del backend.

No crees todavía modelos de `users`, `sites`, etc. Eso pertenece a issues posteriores.

---

# Área 5 — Crear `config.py`

**Tiempo estimado: 30–45 min**

Responsabilidad:

```text
leer configuración
      ↓
entregarla al backend
```

Debe concentrar cosas como:

```text
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
POSTGRES_HOST
POSTGRES_PORT
```

y permitir construir:

```text
DATABASE_URL
```

Ejemplo conceptual:

```text
postgresql+driver://user:password@database:5432/aquaguard
```

### Lo que debes entender aquí

Dentro de Docker:

```text
POSTGRES_HOST=database
```

No:

```text
POSTGRES_HOST=localhost
```

Porque:

```text
backend container
    ↓
localhost
    ↓
backend container
```

Mientras:

```text
backend container
    ↓
database
    ↓
PostgreSQL container
```

### Fin del área

Debes poder imprimir o inspeccionar la configuración **sin mostrar la password** y comprobar que el host es correcto.

---

# Área 6 — Crear el SQLAlchemy Engine

**Tiempo estimado: 30–45 min**

Ahora empieza realmente la integración.

En:

```text
backend/app/core/database.py
```

tu primera responsabilidad será crear:

```text
Engine
```

Modelo mental:

```text
DATABASE_URL
     ↓
create_engine(...)
     ↓
Engine
     ↓
connection pool
```

El Engine:

* conoce dónde está PostgreSQL;
* utiliza el driver;
* mantiene/administra conexiones;
* será compartido por la aplicación.

### Primera prueba

Antes incluso de las sesiones, comprueba:

```text
Engine
   ↓
PostgreSQL
   ↓
SELECT 1
```

Si esto falla, todavía no tiene sentido seguir con `Session`.

### Fin del área

Debes poder afirmar:

```text
SQLAlchemy Engine puede conectarse a PostgreSQL.
```

---

# Área 7 — Configurar sesiones SQLAlchemy

**Tiempo estimado: 45 min**

Ahora añade:

```text
sessionmaker
```

Modelo:

```text
Engine
  ↓
SessionLocal factory
  ↓
Session
```

Importante:

```text
SessionLocal != Session
```

`SessionLocal` es la fábrica.

Ejemplo conceptual:

```text
SessionLocal()
    ↓
Session concreta
```

Debes preparar una función equivalente a:

```text
get_db()
```

Flujo:

```text
crear session
    ↓
yield
    ↓
usar DB
    ↓
close
```

### Prueba

Abre una sesión manualmente y ejecuta:

```sql
SELECT 1
```

Después ciérrala.

### Fin del área

Debes saber explicar:

```text
¿Por qué no usamos directamente el Engine en toda la aplicación?

Porque la Session representa una unidad de trabajo y ofrece una interfaz ORM/transaccional más adecuada para las operaciones de negocio.
```

---

# Área 8 — Estrategia básica de transacciones

**Tiempo estimado: 30–45 min**

Define vuestra regla básica antes de crear repositories.

La estrategia inicial puede ser:

```text
operación correcta
      ↓
commit

operación incorrecta
      ↓
rollback

siempre
      ↓
close
```

Debes entender muy bien estas tres funciones:

```text
commit()
→ confirma los cambios

rollback()
→ revierte la transacción actual

close()
→ cierra/libera la sesión
```

### Regla recomendada

No hagas:

```text
commit automático después de cada pequeña consulta
```

Piensa más bien:

```text
una operación de negocio
=
una transacción
```

Aunque la lógica de negocio la implemente Ana más adelante, tú dejas definida esta estrategia base para que los repositories/services puedan utilizarla.

---

# Área 9 — Integrarlo con FastAPI

**Tiempo estimado: 30–45 min**

Ahora conecta:

```text
FastAPI
   ↓
Session
   ↓
Engine
   ↓
PostgreSQL
```

No necesitas implementar endpoints del producto.

Puedes realizar una comprobación técnica mínima durante desarrollo:

```text
FastAPI arranca
    ↓
obtiene sesión
    ↓
SELECT 1
    ↓
resultado correcto
```

Lo importante es demostrar:

```text
FastAPI tiene acceso a PostgreSQL utilizando SQLAlchemy.
```

Una vez demostrado, no conviertas esta issue en una issue de endpoints.

---

# Área 10 — Integración backend + database en Docker

**Tiempo estimado: 45–60 min**

Ahora llega una prueba importante:

```text
docker compose
├── backend
└── database
```

La red será aproximadamente:

```text
┌──────────────────────────────────┐
│        Docker network            │
│                                  │
│ FastAPI              PostgreSQL  │
│ backend ───────────→ database    │
│ :8000                :5432       │
│                                  │
└──────────────────────────────────┘
```

Levanta los dos juntos:

```bash
docker compose up --build
```

Comprueba:

* [ ] database arranca.
* [ ] database está healthy.
* [ ] backend arranca.
* [ ] backend resuelve hostname `database`.
* [ ] SQLAlchemy crea conexión.
* [ ] FastAPI no falla al iniciar.
* [ ] `SELECT 1` funciona.

Este es prácticamente el corazón de tu criterio de aceptación.

---

# Área 11 — Tests manuales de errores

**Tiempo estimado: 30 min**

No pruebes únicamente el caso feliz.

## Prueba 1 — password incorrecta

Temporalmente pon una password incorrecta.

Esperas:

```text
conexión rechazada
```

## Prueba 2 — host incorrecto

Cambiar temporalmente:

```text
database
```

por:

```text
database-fake
```

Esperas:

```text
error de resolución/conexión
```

## Prueba 3 — PostgreSQL apagado

Detén DB y arranca backend.

Debes entender qué error produce.

## Prueba 4 — Restaurar configuración correcta

Finalmente devuelve todo al estado válido.

No commits los cambios de las pruebas destructivas.

---

# Área 12 — Revisión antes del Pull Request

**Tiempo estimado: 30–45 min**

Haz esta revisión completa.

## PostgreSQL

* [ ] PostgreSQL arranca correctamente.
* [ ] Tiene volumen persistente.
* [ ] Tiene configuración vía entorno.
* [ ] Healthcheck correcto.

## SQLAlchemy

* [ ] Engine configurado.
* [ ] Session factory configurada.
* [ ] Sesión se abre correctamente.
* [ ] Sesión se cierra correctamente.

## Transacciones

* [ ] Estrategia `commit`.
* [ ] Estrategia `rollback`.
* [ ] Estrategia `close`.

## FastAPI

* [ ] Arranca.
* [ ] Se conecta a DB.
* [ ] Ejecuta una consulta simple.

## Seguridad

* [ ] `.env` ignorado.
* [ ] `.env.example` disponible.
* [ ] No passwords hardcodeadas.
* [ ] `git diff` no contiene credenciales.

## Git

* [ ] Commits pequeños y entendibles.
* [ ] No has metido modelos o endpoints que no pertenecen a esta issue.
* [ ] PR hacia `develop`.
* [ ] Issue enlazada.

---

# Plan temporal recomendado

Si tienes unas **5–7 horas reales**, puedes organizarlo así:

## Bloque 1 — 1 hora

```text
Comprensión
+
PostgreSQL Docker
```

Objetivo:

```text
DB healthy
```

## Bloque 2 — 1 hora

```text
.env
+
.env.example
+
config.py
+
dependencias
```

Objetivo:

```text
configuración centralizada
```

## Bloque 3 — 1–1.5 horas

```text
Engine
+
driver
+
SELECT 1
```

Objetivo:

```text
SQLAlchemy → PostgreSQL
```

## Descanso

Conviene hacer una pausa corta aquí porque la siguiente parte introduce otro concepto.

## Bloque 4 — 1 hora

```text
SessionLocal
+
get_db
+
transacciones
```

Objetivo:

```text
gestión correcta de sesiones
```

## Bloque 5 — 1 hora

```text
FastAPI
+
Docker backend/database
```

Objetivo:

```text
FastAPI → PostgreSQL
```

## Bloque 6 — 30–60 min

```text
errores
+
seguridad
+
limpieza
+
PR
```

Objetivo:

```text
criterios de aceptación completos
```

---

# Orden exacto que te recomiendo seguir

No intentes resolver todo a la vez. Sigue este orden:

```text
1. Docker PostgreSQL
       ↓
2. PostgreSQL healthy
       ↓
3. .env / .env.example
       ↓
4. instalar SQLAlchemy + driver
       ↓
5. config.py
       ↓
6. DATABASE_URL
       ↓
7. Engine
       ↓
8. SELECT 1 mediante Engine
       ↓
9. SessionLocal
       ↓
10. SELECT 1 mediante Session
       ↓
11. commit / rollback / close
       ↓
12. integrar con FastAPI
       ↓
13. backend + DB mediante Compose
       ↓
14. revisar secretos
       ↓
15. Pull Request
```

---

# Lo que NO debes hacer todavía

Para mantener esta issue pequeña, evita empezar:

* [ ] tabla `organizations`.
* [ ] tabla `users`.
* [ ] tabla `sites`.
* [ ] tabla `sensors`.
* [ ] tabla `readings`.
* [ ] tabla `alerts`.
* [ ] Alembic completo.
* [ ] repositories de negocio.
* [ ] endpoints `/api/sensors`.
* [ ] Pydantic schemas.
* [ ] autenticación.
* [ ] reglas de alertas.

Todo eso llegará después.

Tu issue termina cuando exista una infraestructura sólida sobre la que luego puedan construirse esas funcionalidades.

---

# Tu definición mental de “he terminado”

Cuando puedas explicar esto sin mirar código:

```text
Docker Compose levanta PostgreSQL.

FastAPI obtiene su configuración desde variables
de entorno.

SQLAlchemy crea un Engine utilizando la
DATABASE_URL.

El Engine utiliza un driver PostgreSQL para
comunicarse con la DB.

SessionLocal crea sesiones asociadas al Engine.

Cada operación puede hacer commit o rollback.

La sesión siempre termina cerrándose.

FastAPI puede utilizar esa sesión para llegar
hasta PostgreSQL.

Las credenciales reales no están en Git.
```

entonces no solo habrás terminado técnicamente la issue: **también entenderás lo que has implementado**, que es especialmente importante para la evaluación del proyecto.
