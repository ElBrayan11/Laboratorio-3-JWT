from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user, hash_password

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

ROLES_VALIDOS = [
    "solicitante",
    "responsable_tecnico",
    "auxiliar",
    "tecnico_especializado",
    "admin",
]


@router.post("/", response_model=schemas.UsuarioOut, status_code=201)
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    """
    Endpoint público para registrar nuevos usuarios.
    La contraseña se almacena como hash bcrypt; nunca en texto plano.
    """
    existente = (
        db.query(models.Usuario)
        .filter(models.Usuario.correo == usuario.correo)
        .first()
    )
    if existente:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    if usuario.rol not in ROLES_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Rol inválido. Opciones permitidas: {ROLES_VALIDOS}",
        )

    db_usuario = models.Usuario(
        nombre=usuario.nombre,
        correo=usuario.correo,
        password_hash=hash_password(usuario.password),
        rol=usuario.rol,
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario


@router.get("/", response_model=List[schemas.UsuarioOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Security(
        get_current_user, scopes=["usuarios:gestionar"]
    ),
):
    """Solo el rol admin puede listar todos los usuarios."""
    return db.query(models.Usuario).all()


@router.get("/{id_usuario}", response_model=schemas.UsuarioOut)
def obtener_usuario(
    id_usuario: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Security(
        get_current_user, scopes=["usuarios:gestionar"]
    ),
):
    """Solo el rol admin puede consultar un usuario por ID."""
    usuario = (
        db.query(models.Usuario)
        .filter(models.Usuario.id_usuario == id_usuario)
        .first()
    )
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario
