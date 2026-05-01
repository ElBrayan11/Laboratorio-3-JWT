from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

SCHEMA = "jwt_grupo_8"


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = {"schema": SCHEMA}

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    correo = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    rol = Column(String, nullable=False)
    activo = Column(Boolean, default=True)

    tickets_solicitados = relationship(
        "Ticket", foreign_keys="Ticket.id_solicitante", back_populates="solicitante"
    )
    tickets_responsable = relationship(
        "Ticket", foreign_keys="Ticket.id_responsable", back_populates="responsable"
    )
    tickets_asignados = relationship(
        "Ticket", foreign_keys="Ticket.id_asignado", back_populates="asignado"
    )


class Laboratorio(Base):
    __tablename__ = "laboratorios"
    __table_args__ = {"schema": SCHEMA}

    id_laboratorio = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    ubicacion = Column(String, nullable=False)
    activo = Column(Boolean, default=True)

    tickets = relationship("Ticket", back_populates="laboratorio")


class Servicio(Base):
    __tablename__ = "servicios"
    __table_args__ = {"schema": SCHEMA}

    id_servicio = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)

    tickets = relationship("Ticket", back_populates="servicio")


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = {"schema": SCHEMA}

    id_ticket = Column(Integer, primary_key=True, index=True)
    id_solicitante = Column(Integer, ForeignKey(f"{SCHEMA}.usuarios.id_usuario"), nullable=False)
    id_laboratorio = Column(Integer, ForeignKey(f"{SCHEMA}.laboratorios.id_laboratorio"), nullable=False)
    id_servicio = Column(Integer, ForeignKey(f"{SCHEMA}.servicios.id_servicio"), nullable=False)
    id_responsable = Column(Integer, ForeignKey(f"{SCHEMA}.usuarios.id_usuario"), nullable=True)
    id_asignado = Column(Integer, ForeignKey(f"{SCHEMA}.usuarios.id_usuario"), nullable=True)

    titulo = Column(String, nullable=False)
    descripcion = Column(Text, nullable=False)
    estado = Column(String, default="solicitado")
    prioridad = Column(String, default="media")
    observacion_responsable = Column(Text, nullable=True)
    observacion_tecnico = Column(Text, nullable=True)

    fecha_creacion = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())
    fecha_finalizacion = Column(DateTime, nullable=True)

    solicitante = relationship("Usuario", foreign_keys=[id_solicitante], back_populates="tickets_solicitados")
    responsable = relationship("Usuario", foreign_keys=[id_responsable], back_populates="tickets_responsable")
    asignado = relationship("Usuario", foreign_keys=[id_asignado], back_populates="tickets_asignados")
    laboratorio = relationship("Laboratorio", back_populates="tickets")
    servicio = relationship("Servicio", back_populates="tickets")
