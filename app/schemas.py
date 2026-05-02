from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ─── USUARIOS ────────────────────────────────────────────────────────────────

class UsuarioCreate(BaseModel):
    nombre: str
    correo: str
    password: str
    rol: str


class UsuarioOut(BaseModel):
    id_usuario: int
    nombre: str
    correo: str
    rol: str
    activo: bool

    class Config:
        from_attributes = True


# ─── LABORATORIOS ─────────────────────────────────────────────────────────────

class LaboratorioCreate(BaseModel):
    nombre: str
    ubicacion: str
    activo: Optional[bool] = True


class LaboratorioOut(LaboratorioCreate):
    id_laboratorio: int

    class Config:
        from_attributes = True


# ─── SERVICIOS ────────────────────────────────────────────────────────────────

class ServicioCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    activo: Optional[bool] = True


class ServicioOut(ServicioCreate):
    id_servicio: int

    class Config:
        from_attributes = True


# ─── TICKETS ──────────────────────────────────────────────────────────────────

class TicketCreate(BaseModel):
    id_laboratorio: int
    id_servicio: int
    titulo: str
    descripcion: str
    prioridad: Optional[str] = "media"


class TicketOut(BaseModel):
    id_ticket: int
    id_solicitante: int
    id_laboratorio: int
    id_servicio: int
    id_responsable: Optional[int]
    id_asignado: Optional[int]
    titulo: str
    descripcion: str
    estado: str
    prioridad: str
    observacion_responsable: Optional[str]
    observacion_tecnico: Optional[str]
    fecha_creacion: Optional[datetime]
    fecha_actualizacion: Optional[datetime]
    fecha_finalizacion: Optional[datetime]

    class Config:
        from_attributes = True


class TicketCambioEstado(BaseModel):
    nuevo_estado: str
    id_asignado: Optional[int] = None
    observacion_responsable: Optional[str] = None
    observacion_tecnico: Optional[str] = None


# ─── AUTH ─────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    correo: Optional[str] = None
    id_usuario: Optional[int] = None
    rol: Optional[str] = None
    scopes: List[str] = []
