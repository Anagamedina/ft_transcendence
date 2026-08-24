### 1. ¿Qué es PostgreSQL?

**PostgreSQL es el sistema gestor de base de datos.**

Es el programa que realmente almacena y organiza los datos persistentes de AquaGuard.

Por ejemplo, terminará almacenando tablas como:

```text
users
organizations
sites
sensors
readings
alerts
```

Conceptualmente:

```text
PostgreSQL
    ├── users
    ├── sites
    ├── sensors
    ├── readings
    └── alerts
```

PostgreSQL estará dentro del contenedor `database` y sus datos estarán en un **volumen persistente de Docker**.

---

### 2. ¿Qué es un driver PostgreSQL?

Es la **librería que permite que Python se comunique realmente con PostgreSQL**.

SQLAlchemy por sí solo no habla directamente el protocolo de PostgreSQL, y necesita un driver.

Por ejemplo:

```text
SQLAlchemy
     ↓
PostgreSQL driver
     ↓
PostgreSQL
```

Dependiendo de si se elije utilizar la forma síncrona o asíncrona:

```text
psycopg
asyncpg
```

Una URL de conexión puede reflejarlo:

```text
postgresql+psycopg://user:password@database:5432/aquaguard
           ↑
         driver
```

Piensa en el driver como el **traductor/conector técnico entre Python y PostgreSQL**.

---



### 3. ¿Qué hace SQLAlchemy?

**SQLAlchemy es la capa de acceso a datos que utilizará vuestro backend Python.**

En vuestro documento está definido como el ORM del proyecto.

En lugar de trabajar constantemente con SQL directamente:

```sql
SELECT * FROM sensors WHERE id = 4;
```

puedes trabajar con objetos/modelos Python:

```python
sensor = session.get(Sensor, 4)
```

SQLAlchemy se ocupa de convertir esas operaciones en consultas que PostgreSQL entiende.

Por eso vuestro flujo es:

```text
Repository
    ↓
SQLAlchemy
    ↓
PostgreSQL
```

Además, SQLAlchemy gestiona conexiones, sesiones, transacciones, modelos y relaciones.

---

### 4. Diferencia entre `Engine` y `Session`

Esta diferencia es **muy importante**.

El `Engine` representa la infraestructura de conexión con la base de datos.

```python
engine = create_engine(DATABASE_URL)
```

Conceptualmente:

```text
Engine
  ↓
pool de conexiones
  ↓
driver
  ↓
PostgreSQL
```

Normalmente creas **un Engine para toda la aplicación**.

La `Session`, en cambio, representa una **unidad de trabajo con la base de datos**.

```python
session.add(sensor)
session.commit()
```

Por ejemplo:

```text
FastAPI
   ↓
Session
   ↓
Engine
   ↓
Driver
   ↓
PostgreSQL
```

Regla mental:

> **Engine = cómo puedo conectarme a PostgreSQL.**
 
> **Session = conversación/unidad de trabajo que estoy realizando con PostgreSQL.**

---

### 5. ¿Qué significa `commit`?

`commit` significa:

> **Confirmar definitivamente los cambios de una transacción.**

Por ejemplo:

```python
sensor = Sensor(name="Sensor cocina")

session.add(sensor)
session.commit()
```

Hasta que se confirma correctamente la transacción, ese conjunto de cambios no debe considerarse terminado.

Mentalmente:

```text
INSERT sensor
      ↓
transacción
      ↓
commit()
      ↓
CAMBIOS CONFIRMADOS
```

---



### 6. ¿Qué significa `rollback`?

Es lo contrario ante un fallo:

> **Deshacer los cambios pendientes de la transacción.**

Ejemplo conceptual:

```python
try:
    session.add(sensor)
    session.commit()
except:
    session.rollback()
```

Imagina que haces varias operaciones:

```text
crear Reading
crear Alert
actualizar Sensor
```

y algo falla.

En lugar de dejar una operación a medias:

```text
ERROR
 ↓
rollback
 ↓
volver al estado anterior
```

Esto es especialmente importante porque vuestro documento exige una DB transaccional y funcionamiento correcto con múltiples usuarios.

---



### 7. ¿Qué significa `close`?

`close()` significa:

> **Terminar el uso de una Session y liberar sus recursos/conexiones asociados para que puedan reutilizarse correctamente.**

Un patrón conceptual sería:

```python
session = Session()

try:
    ...
finally:
    session.close()
```

No confundas:

```text
commit   → confirma cambios
rollback → deshace cambios pendientes
close    → termina/libera la sesión
```

`close()` **no significa apagar PostgreSQL**.

---



### 8. ¿Qué es una variable de entorno?

Es una configuración que existe **fuera del código fuente** y que el programa puede leer.

Por ejemplo, en lugar de escribir:

```python
password = "mi_password_supersecreto"
```

tu aplicación podría obtener:

```text
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
DATABASE_URL
```

y Python leer esos valores.

Esto permite que el mismo código funcione en:

```text
desarrollo
testing
producción
Docker
```

cambiando configuración sin modificar el código.

---



### 9. ¿Por qué `.env` no debe subirse a Git?

Porque normalmente contiene **secretos o configuración privada**:

```env
POSTGRES_USER=aquaguard
POSTGRES_PASSWORD=super_secret_password
DATABASE_URL=...
SECRET_KEY=...
```

Si haces:

```bash
git add .
git commit
git push
```

y `.env` está versionado, las credenciales pueden acabar en el historial de Git.

Por eso vuestro documento exige explícitamente:

```text
.env          → NO Git
.env.example  → SÍ Git
```

y `../../.gitignore` debería incluir:

```gitignore
.env
```

Mientras que `.env.example` contiene únicamente una plantilla:

```env
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
DATABASE_URL=
```

Esto forma parte de los requisitos Mandatory de AquaGuard: **no versionar secretos reales**.

---



### 10. ¿Qué es una red de Docker Compose?

Es una **red virtual privada** mediante la cual los contenedores pueden comunicarse entre ellos.

En AquaGuard tendréis algo conceptualmente parecido a:

```text
       Docker Compose network
┌─────────────────────────────────┐
│                                 │
│ backend ──────────► database    │
│ FastAPI             PostgreSQL  │
│ :8000                :5432      │
│                                 │
│ simulator ─────────► backend    │
│                                 │
└─────────────────────────────────┘
```

Lo importante es que dentro de Compose los servicios pueden localizarse utilizando **el nombre del servicio**.

Por ejemplo, si vuestro `../../compose.yaml` tiene:

```yaml
services:

  backend:
    ...

  database:
    image: postgres
```

FastAPI puede conectarse usando:

```text
database:5432
```

en vez de:

```text
localhost:5432
```

Esto es crucial:

> Dentro del contenedor `backend`, `localhost` significa **el propio contenedor backend**, no PostgreSQL.

Vuestro documento establece precisamente que **backend (8000) y PostgreSQL (5432) permanecen en la red interna de Compose**, mientras que finalmente el `gateway` será quien exponga la aplicación al exterior.

---



### El mapa mental que quiero que tengas antes de programar

Juntando todo:

```text
                    FASTAPI
                       │
                       │ solicita Session
                       ▼
                   SESSION
              unidad de trabajo
                       │
          ┌────────────┼────────────┐
          │            │            │
       commit       rollback      close
       confirma      deshace      libera
          │
          ▼
                    ENGINE
            infraestructura conexión
                       │
                       ▼
               PostgreSQL DRIVER
                       │
                Docker Network
                       │
                       ▼
                  POSTGRESQL
                       │
                       ▼
              datos persistentes
```

Y alrededor de todo eso:

```text
.env
 │
 ├── POSTGRES_USER
 ├── POSTGRES_PASSWORD
 ├── POSTGRES_DB
 └── DATABASE_URL
```

Si entiendes especialmente `Session → Engine → Driver → PostgreSQL` y `commit / rollback / close`, ya tienes la base conceptual necesaria para empezar a implementar `../../backend/app/core/database.py` con bastante más sentido.