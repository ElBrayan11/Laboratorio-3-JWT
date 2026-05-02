from fastapi import FastAPI
from app.database import engine, Base
from app.routers import auth_router, usuarios, laboratorios, servicios, tickets

# Crea todas las tablas en el schema jwt_grupo_8 si no existen.
# SQLAlchemy lee los modelos importados y ejecuta CREATE TABLE IF NOT EXISTS
# dentro del schema especificado en __table_args__.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Mesa de Servicios — Taller 3",
    description=(
        "API para gestión de tickets de servicios en laboratorios universitarios.\n\n"
        "**Flujo de autenticación en Swagger:**\n"
        "1. Crea un usuario con `POST /usuarios/`.\n"
        "2. Inicia sesión con `POST /auth/token`.\n"
        "3. Copia el `access_token` y haz clic en **Authorize** → `Bearer <token>`.\n"
        "4. Ahora puedes usar los endpoints protegidos."
    ),
    version="1.0.0",
)

app.include_router(auth_router.router)
app.include_router(usuarios.router)
app.include_router(laboratorios.router)
app.include_router(servicios.router)
app.include_router(tickets.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "mensaje": "API Taller 3 — JWT + Scopes + FastAPI ",
        "docs": "/docs",
        "redoc": "/redoc",
    }
