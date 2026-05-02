from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user

router = APIRouter(prefix="/servicios", tags=["Servicios"])


@router.post("/", response_model=schemas.ServicioOut, status_code=201)
def crear_servicio(
    servicio: schemas.ServicioCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Security(
        get_current_user, scopes=["usuarios:gestionar"]
    ),
):
    """Solo admin puede registrar tipos de servicio."""
    db_servicio = models.Servicio(**servicio.model_dump())
    db.add(db_servicio)
    db.commit()
    db.refresh(db_servicio)
    return db_servicio


@router.get("/", response_model=List[schemas.ServicioOut])
def listar_servicios(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Cualquier usuario autenticado puede consultar los servicios disponibles."""
    return db.query(models.Servicio).filter(models.Servicio.activo == True).all()


@router.get("/{id_servicio}", response_model=schemas.ServicioOut)
def obtener_servicio(
    id_servicio: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    s = (
        db.query(models.Servicio)
        .filter(models.Servicio.id_servicio == id_servicio)
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return s
