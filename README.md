# Mesa de Servicios — Taller 3: JWT, Scopes y FastAPI

## Integrantes

| Nombre completo | Usuarios |
|---|---|
| Santiago Orrego Castaño | 1803790 |
| Brayan David Mejia Serna | ElBrayan11 |
| Ivan Andrés Blanco Velasquez | Blocweb |

---

## Descripción

API REST para la gestión de tickets de soporte técnico en laboratorios universitarios, desarrollada con FastAPI y PostgreSQL. Implementa autenticación mediante JSON Web Tokens (JWT) y autorización basada en scopes según el rol del usuario.

---

## Instalación y ejecución

```bash
# Clonar el repositorio
git clone https://github.com/ElBrayan11/Laboratorio-3-JWT.git
cd taller3_jwt

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env

# Correr el servidor
uvicorn app.main:app --reload
```

Documentación interactiva disponible en: http://127.0.0.1:8000/docs

---

## Variables de entorno (.env)
DATABASE_URL=postgresql://admin:admin@190.248.28.132:3010/dbapps
SECRET_KEY=super_clave_secreta_taller3_jwt_grupo8
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

> El archivo `.env` no se sube al repositorio. Está incluido en `.gitignore`.

---

## Estructura del proyecto
taller3_jwt/
├── app/
│   ├── main.py           # Punto de entrada FastAPI
│   ├── database.py       # Conexión PostgreSQL y sesión
│   ├── models.py         # Modelos SQLAlchemy (tablas)
│   ├── schemas.py        # Esquemas Pydantic (validación)
│   ├── auth.py           # JWT, bcrypt, dependencias de seguridad
│   └── routers/
│       ├── auth_router.py
│       ├── usuarios.py
│       ├── laboratorios.py
│       ├── servicios.py
│       └── tickets.py
├── .env.example
├── .gitignore
└── requirements.txt

---

## Base de datos

- Motor: PostgreSQL
- Schema asignado: `jwt_grupo_8`
- Las tablas se crean automáticamente al iniciar la aplicación.

---

## Endpoints

| Método | Ruta | Descripción | Scope requerido |
|---|---|---|---|
| POST | `/auth/token` | Login, devuelve JWT | Público |
| POST | `/usuarios/` | Registrar usuario | Público |
| GET | `/usuarios/` | Listar todos los usuarios | `usuarios:gestionar` |
| GET | `/usuarios/{id}` | Consultar usuario por ID | `usuarios:gestionar` |
| POST | `/laboratorios/` | Crear laboratorio | `usuarios:gestionar` |
| GET | `/laboratorios/` | Listar laboratorios | Autenticado |
| GET | `/laboratorios/{id}` | Consultar laboratorio | Autenticado |
| POST | `/servicios/` | Crear servicio | `usuarios:gestionar` |
| GET | `/servicios/` | Listar servicios | Autenticado |
| GET | `/servicios/{id}` | Consultar servicio | Autenticado |
| POST | `/tickets/` | Crear ticket | `tickets:crear` |
| GET | `/tickets/` | Listar tickets (filtrado por rol) | `tickets:ver_propios` |
| GET | `/tickets/{id}` | Consultar ticket | `tickets:ver_propios` |
| PATCH | `/tickets/{id}/estado` | Cambiar estado del ticket | Según transición |

---

## Roles y Scopes

| Rol | Scopes asignados |
|---|---|
| `solicitante` | `tickets:crear`, `tickets:ver_propios` |
| `responsable_tecnico` | `tickets:ver_propios`, `tickets:recibir`, `tickets:asignar`, `tickets:finalizar` |
| `auxiliar` | `tickets:ver_propios`, `tickets:atender` |
| `tecnico_especializado` | `tickets:ver_propios`, `tickets:atender` |
| `admin` | Todos los scopes anteriores + `tickets:ver_todos`, `usuarios:gestionar` |

---

## Flujo de estados del ticket

solicitado → recibido → asignado → en_proceso → en_revision → terminado

| Transición | Scope requerido | Restricción adicional |
|---|---|---|
| `solicitado` → `recibido` | `tickets:recibir` | responsable_tecnico o admin |
| `recibido` → `asignado` | `tickets:asignar` | responsable_tecnico o admin; requiere `id_asignado` |
| `asignado` → `en_proceso` | `tickets:atender` | Solo el técnico asignado al ticket |
| `en_proceso` → `en_revision` | `tickets:atender` | Solo el técnico asignado al ticket |
| `en_revision` → `terminado` | `tickets:finalizar` | responsable_tecnico o admin |

---

## Evidencias de pruebas

Se subieron las evidencias de prueba del funcionamiento del sistema en la carpeta evindencias 

---

## Aportes por integrante

**Brayan David Mejia Serna**
- Implementó `database.py` (conexión a PostgreSQL y sesión con SQLAlchemy)
- Implementó `models.py` (modelos de Usuario, Laboratorio, Servicio y Ticket)
- Configuró el schema `jwt_grupo_8` en todos los modelos
- Commits: `feat: db connection`, `feat: db models`, `feat: schema jwt_grupo_8`

**Iván Andrés Blanco Velásquez**
- Implementó `schemas.py` (esquemas Pydantic para validación de datos)
- Implementó `auth.py` (JWT, bcrypt, scopes por rol y dependencia `get_current_user`)
- Implementó `auth_router.py` (endpoint de login `/auth/token`)
- Commits: `feat: pydantic schemas`, `feat: jwt auth`, `feat: scopes por rol`

**Santiago Orrego Castaño**
- Implementó `routers/usuarios.py`, `routers/laboratorios.py` y `routers/servicios.py`
- Implementó `routers/tickets.py` con flujo de estados y tabla de transiciones
- Implementó `main.py` (registro de routers y creación de tablas)
- Commits: `feat: usuarios router`, `feat: tickets router`, `feat: state machine`

---

## Conclusiones

- **JWT** permite autenticación stateless: el servidor no necesita guardar sesiones, toda la información del usuario viaja firmada dentro del token.
- **Scopes** permiten autorización granular: en lugar de solo verificar si el usuario está autenticado, se verifica exactamente qué acciones puede realizar.
- **FastAPI** integra OAuth2 con scopes de forma nativa, lo que facilita documentar y probar la seguridad directamente desde Swagger.
- El patrón de **flujo de estados** en tickets garantiza que ningún usuario pueda saltar pasos ni modificar tickets que no le corresponden según su rol.
