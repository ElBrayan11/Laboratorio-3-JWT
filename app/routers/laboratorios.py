from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user

router = APIRouter(prefix="/laboratorios", tags=["Laboratorios"])


@router.post("/", response_model=schemas.LaboratorioOut, status_code=201)
def crear_laboratorio(
    lab: schemas.LaboratorioCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Security(
        get_current_user, scopes=["usuarios:gestionar"]
    ),
):
    """Solo admin puede registrar laboratorios."""
    db_lab = models.Laboratorio(**lab.model_dump())
    db.add(db_lab)
    db.commit()
    db.refresh(db_lab)
    return db_lab


@router.get("/", response_model=List[schemas.LaboratorioOut])
def listar_laboratorios(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Cualquier usuario autenticado puede consultar los laboratorios."""
    return db.query(models.Laboratorio).filter(models.Laboratorio.activo == True).all()


@router.get("/{id_laboratorio}", response_model=schemas.LaboratorioOut)
def obtener_laboratorio(
    id_laboratorio: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    lab = (
        db.query(models.Laboratorio)
        .filter(models.Laboratorio.id_laboratorio == id_laboratorio)
        .first()
    )
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratorio no encontrado")
    return lab
