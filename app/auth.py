from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

from app.database import get_db
from app import models, schemas

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# ─── SCOPES POR ROL ──────────────────────────────────────────────────────────

SCOPES_POR_ROL = {
    "solicitante": [
        "tickets:crear",
        "tickets:ver_propios",
    ],
    "responsable_tecnico": [
        "tickets:ver_propios",
        "tickets:recibir",
        "tickets:asignar",
        "tickets:finalizar",
    ],
    "auxiliar": [
        "tickets:ver_propios",
        "tickets:atender",
    ],
    "tecnico_especializado": [
        "tickets:ver_propios",
        "tickets:atender",
    ],
    "admin": [
        "tickets:crear",
        "tickets:ver_propios",
        "tickets:ver_todos",
        "tickets:recibir",
        "tickets:asignar",
        "tickets:atender",
        "tickets:finalizar",
        "usuarios:gestionar",
    ],
}

# ─── HASHING ─────────────────────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ─── OAUTH2 ──────────────────────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    scopes={
        "tickets:crear": "Crear tickets",
        "tickets:ver_propios": "Ver propios tickets",
        "tickets:ver_todos": "Ver todos los tickets",
        "tickets:recibir": "Recibir tickets (solicitado → recibido)",
        "tickets:asignar": "Asignar tickets (recibido → asignado)",
        "tickets:atender": "Atender tickets (asignado → en_proceso → en_revision)",
        "tickets:finalizar": "Finalizar tickets (en_revision → terminado)",
        "usuarios:gestionar": "Gestionar usuarios",
    },
)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ─── DEPENDENCIA PRINCIPAL ───────────────────────────────────────────────────

async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.Usuario:
    """
    Dependencia reutilizable en todos los endpoints protegidos.
    - Valida la firma y expiración del JWT.
    - Verifica que el token contiene los scopes requeridos por el endpoint.
    - Devuelve el objeto Usuario activo desde la BD.
    """
    authenticate_value = (
        f'Bearer scope="{security_scopes.scope_str}"'
        if security_scopes.scopes
        else "Bearer"
    )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        correo: str = payload.get("sub")
        if correo is None:
            raise credentials_exception

        token_scopes = payload.get("scopes", [])
        token_data = schemas.TokenData(
            correo=correo,
            id_usuario=payload.get("id_usuario"),
            rol=payload.get("rol"),
            scopes=token_scopes,
        )
    except JWTError:
        raise credentials_exception

    usuario = (
        db.query(models.Usuario)
        .filter(models.Usuario.correo == token_data.correo)
        .first()
    )

    if usuario is None or not usuario.activo:
        raise credentials_exception

    # Verificar cada scope requerido por el endpoint
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere el permiso: '{scope}'",
                headers={"WWW-Authenticate": authenticate_value},
            )

    return usuario
