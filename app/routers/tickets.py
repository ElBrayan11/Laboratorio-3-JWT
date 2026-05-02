from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user, SCOPES_POR_ROL

router = APIRouter(prefix="/tickets", tags=["Tickets"])

# ─── TABLA DE TRANSICIONES ────────────────────────────────────────────────────
# Define el flujo de estados válido del ticket.
# solo_asignado=True significa que únicamente el técnico asignado
# al ticket puede ejecutar esa transición (a menos que sea admin).
TRANSICIONES = {
    "solicitado": {
        "siguiente": "recibido",
        "scope": "tickets:recibir",
        "solo_asignado": False,
    },
    "recibido": {
        "siguiente": "asignado",
        "scope": "tickets:asignar",
        "solo_asignado": False,
    },
    "asignado": {
        "siguiente": "en_proceso",
        "scope": "tickets:atender",
        "solo_asignado": True,
    },
    "en_proceso": {
        "siguiente": "en_revision",
        "scope": "tickets:atender",
        "solo_asignado": True,
    },
    "en_revision": {
        "siguiente": "terminado",
        "scope": "tickets:finalizar",
        "solo_asignado": False,
    },
}


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _get_ticket_o_404(id_ticket: int, db: Session) -> models.Ticket:
    ticket = db.query(models.Ticket).filter(models.Ticket.id_ticket == id_ticket).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ticket


def _get_user_scopes(usuario: models.Usuario) -> list:
    return SCOPES_POR_ROL.get(usuario.rol, [])


def _verificar_visibilidad(ticket: models.Ticket, usuario: models.Usuario):
    """
    Reglas de visibilidad:
      - admin          → ve todo
      - responsable    → ve tickets donde es responsable o aún sin responsable
      - auxiliar/tec   → ve solo los tickets asignados a él
      - solicitante    → ve solo sus propios tickets
    """
    scopes = _get_user_scopes(usuario)

    if "tickets:ver_todos" in scopes:
        return

    if usuario.rol == "responsable_tecnico":
        if ticket.id_responsable is not None and ticket.id_responsable != usuario.id_usuario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso a este ticket.",
            )
        return

    if usuario.rol in ["auxiliar", "tecnico_especializado"]:
        if ticket.id_asignado != usuario.id_usuario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes ver tickets asignados a ti.",
            )
        return

    # solicitante
    if ticket.id_solicitante != usuario.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes ver tus propios tickets.",
        )


# ─── ENDPOINTS ────────────────────────────────────────────────────────────────

@router.post("/", response_model=schemas.TicketOut, status_code=201)
def crear_ticket(
    ticket: schemas.TicketCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Security(
        get_current_user, scopes=["tickets:crear"]
    ),
):
    """
    Crea un nuevo ticket en estado 'solicitado'.
    Requiere scope: tickets:crear  (solicitante, admin).
    El id_solicitante se asigna automáticamente desde el token JWT.
    """
    lab = db.query(models.Laboratorio).filter(
        models.Laboratorio.id_laboratorio == ticket.id_laboratorio,
        models.Laboratorio.activo == True,
    ).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratorio no encontrado o inactivo")

    srv = db.query(models.Servicio).filter(
        models.Servicio.id_servicio == ticket.id_servicio,
        models.Servicio.activo == True,
    ).first()
    if not srv:
        raise HTTPException(status_code=404, detail="Servicio no encontrado o inactivo")

    db_ticket = models.Ticket(
        id_solicitante=current_user.id_usuario,
        id_laboratorio=ticket.id_laboratorio,
        id_servicio=ticket.id_servicio,
        titulo=ticket.titulo,
        descripcion=ticket.descripcion,
        prioridad=ticket.prioridad,
        estado="solicitado",
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@router.get("/", response_model=List[schemas.TicketOut])
def listar_tickets(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Security(
        get_current_user, scopes=["tickets:ver_propios"]
    ),
):
    """
    Devuelve tickets según la visibilidad del rol:
    - admin              → todos
    - responsable_tecnico→ tickets donde es responsable + los recién llegados (sin responsable)
    - auxiliar/tecnico   → tickets asignados a él
    - solicitante        → sus propios tickets
    """
    scopes = _get_user_scopes(current_user)

    if "tickets:ver_todos" in scopes:
        return db.query(models.Ticket).all()

    if current_user.rol == "responsable_tecnico":
        return db.query(models.Ticket).filter(
            (models.Ticket.id_responsable == current_user.id_usuario)
            | (models.Ticket.id_responsable == None)
        ).all()

    if current_user.rol in ["auxiliar", "tecnico_especializado"]:
        return db.query(models.Ticket).filter(
            models.Ticket.id_asignado == current_user.id_usuario
        ).all()

    return db.query(models.Ticket).filter(
        models.Ticket.id_solicitante == current_user.id_usuario
    ).all()


@router.get("/{id_ticket}", response_model=schemas.TicketOut)
def obtener_ticket(
    id_ticket: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Security(
        get_current_user, scopes=["tickets:ver_propios"]
    ),
):
    ticket = _get_ticket_o_404(id_ticket, db)
    _verificar_visibilidad(ticket, current_user)
    return ticket


@router.patch("/{id_ticket}/estado", response_model=schemas.TicketOut)
def cambiar_estado(
    id_ticket: int,
    body: schemas.TicketCambioEstado,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Security(
        get_current_user, scopes=["tickets:ver_propios"]
    ),
):
    """
    Cambia el estado del ticket siguiendo el flujo definido.

    Validaciones en orden:
    1. El ticket debe existir.
    2. La transición solicitada debe ser la siguiente válida en el flujo.
    3. El usuario debe tener el scope requerido para esa transición.
    4. Si la transición es 'solo_asignado', el usuario debe ser el técnico asignado.
    5. Reglas específicas: asignar requiere id_asignado válido.
    """
    ticket = _get_ticket_o_404(id_ticket, db)
    nuevo_estado = body.nuevo_estado

    # ── Capa 1: ¿El estado actual tiene transición? ──
    if ticket.estado not in TRANSICIONES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"El ticket está en estado '{ticket.estado}'. No admite más transiciones.",
        )

    regla = TRANSICIONES[ticket.estado]

    # ── Capa 2: ¿Es la transición correcta? ──
    if nuevo_estado != regla["siguiente"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Transición inválida: '{ticket.estado}' → '{nuevo_estado}'. "
                f"Solo se permite '{ticket.estado}' → '{regla['siguiente']}'."
            ),
        )

    # ── Capa 3: ¿El usuario tiene el scope requerido? ──
    user_scopes = _get_user_scopes(current_user)
    if regla["scope"] not in user_scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Acceso denegado. Se requiere el permiso: '{regla['scope']}'",
        )

    # ── Capa 4: ¿Es "solo_asignado" y el usuario es el técnico asignado? ──
    if regla["solo_asignado"] and current_user.rol != "admin":
        if ticket.id_asignado != current_user.id_usuario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el técnico asignado a este ticket puede realizar esta transición.",
            )

    # ── Capa 5: Reglas específicas por transición ──
    if nuevo_estado == "recibido":
        ticket.id_responsable = current_user.id_usuario

    if nuevo_estado == "asignado":
        if not body.id_asignado:
            raise HTTPException(
                status_code=400,
                detail="Debes indicar 'id_asignado' para asignar el ticket.",
            )
        tecnico = db.query(models.Usuario).filter(
            models.Usuario.id_usuario == body.id_asignado,
            models.Usuario.activo == True,
        ).first()
        if not tecnico or tecnico.rol not in ["auxiliar", "tecnico_especializado", "admin"]:
            raise HTTPException(
                status_code=400,
                detail="El usuario asignado debe tener rol auxiliar o tecnico_especializado.",
            )
        ticket.id_asignado = body.id_asignado
        ticket.id_responsable = current_user.id_usuario

    if nuevo_estado == "terminado":
        ticket.fecha_finalizacion = datetime.utcnow()

    # ── Actualizar ticket ──
    ticket.estado = nuevo_estado

    if body.observacion_responsable is not None:
        ticket.observacion_responsable = body.observacion_responsable
    if body.observacion_tecnico is not None:
        ticket.observacion_tecnico = body.observacion_tecnico

    db.commit()
    db.refresh(ticket)
    return ticket
