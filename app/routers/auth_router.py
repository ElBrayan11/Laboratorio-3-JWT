from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app import models, schemas
from app.auth import (
    verify_password,
    create_access_token,
    SCOPES_POR_ROL,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/token", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Inicio de sesión. Devuelve un token JWT con los scopes del rol del usuario.
    En Swagger, usa el botón **Authorize** con el token recibido.
    """
    usuario = (
        db.query(models.Usuario)
        .filter(models.Usuario.correo == form_data.username)
        .first()
    )

    if not usuario or not verify_password(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not usuario.activo:
        raise HTTPException(status_code=400, detail="Usuario inactivo")

    scopes = SCOPES_POR_ROL.get(usuario.rol, [])

    access_token = create_access_token(
        data={
            "sub": usuario.correo,
            "id_usuario": usuario.id_usuario,
            "rol": usuario.rol,
            "scopes": scopes,
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {"access_token": access_token, "token_type": "bearer"}
