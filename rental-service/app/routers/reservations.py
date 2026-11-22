from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth_client import AuthServiceUnavailable, fetch_user
from ..config import settings
from ..database import get_db
from ..deps import STAFF, Principal, get_principal, require_roles
from ..models import Reservation, Vehicle
from ..schemas import CancellationOut, ReservationCreate, ReservationOut
from ..services.availability import BLOCKING_STATUSES, assign_vehicle
from ..services.pricing import cancellation_fee
from ..services.quotes import build_quote
from .pricing import validate_dates

router = APIRouter(prefix="/reservations", tags=["Reservas"])


@router.post("", response_model=ReservationOut, status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: ReservationCreate,
    db: Session = Depends(get_db),
    user: Principal = Depends(require_roles("customer")),
):
    """Motor de reservas: valida cliente (auth-service), límites de negocio, asigna vehículo
    con bloqueo de fila y congela el precio dinámico calculado en ese instante."""
    validate_dates(payload.start_date, payload.end_date)

    # 1) Validación cruzada con el otro microservicio
    try:
        profile = fetch_user(user.id)
    except AuthServiceUnavailable:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "auth-service no disponible, inténtalo más tarde")
    if not profile or not profile["is_active"] or profile["role"] != "customer":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "El cliente no está habilitado para reservar")

    # 2) Límite de reservas vivas por cliente
    active = db.scalar(
        select(func.count(Reservation.id)).where(
            Reservation.customer_id == user.id,
            Reservation.status.in_(BLOCKING_STATUSES),
            Reservation.end_date >= date.today(),
        )
    )
    if active >= settings.max_active_reservations:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Máximo de {settings.max_active_reservations} reservas vigentes por cliente",
        )

    # 3) Selección de vehículo (concreto o por categoría)
    category = payload.category
    if payload.vehicle_id is not None:
        chosen = db.get(Vehicle, payload.vehicle_id)
        if not chosen:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehículo no encontrado")
        category = chosen.category
    vehicle = assign_vehicle(db, payload.start_date, payload.end_date, category, payload.vehicle_id)
    if not vehicle:
        raise HTTPException(status.HTTP_409_CONFLICT, "No hay vehículos disponibles para esas fechas")

    # 4) Precio dinámico congelado en la reserva
    total, breakdown = build_quote(
        db,
        category=vehicle.category,
        base_rate=vehicle.base_daily_rate,
        start=payload.start_date,
        end=payload.end_date,
        extras=payload.extras,
    )
    reservation = Reservation(
        customer_id=user.id,
        vehicle_id=vehicle.id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status="confirmed",
        extras=list(payload.extras),
        quoted_total=total,
        price_breakdown=breakdown,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


@router.get("/me", response_model=list[ReservationOut])
def my_reservations(db: Session = Depends(get_db), user: Principal = Depends(get_principal)):
    stmt = select(Reservation).where(Reservation.customer_id == user.id).order_by(Reservation.start_date.desc())
    return db.scalars(stmt).all()


@router.get("", response_model=list[ReservationOut], dependencies=[Depends(require_roles(*STAFF))])
def list_reservations(status_: str | None = None, vehicle_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(Reservation).order_by(Reservation.start_date.desc())
    if status_:
        stmt = stmt.where(Reservation.status == status_)
    if vehicle_id:
        stmt = stmt.where(Reservation.vehicle_id == vehicle_id)
    return db.scalars(stmt).all()


@router.get("/{reservation_id}", response_model=ReservationOut)
def get_reservation(reservation_id: int, db: Session = Depends(get_db), user: Principal = Depends(get_principal)):
    reservation = db.get(Reservation, reservation_id)
    if not reservation or (user.role not in STAFF and reservation.customer_id != user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reserva no encontrada")
    return reservation


@router.post("/{reservation_id}/cancel", response_model=CancellationOut)
def cancel_reservation(reservation_id: int, db: Session = Depends(get_db), user: Principal = Depends(get_principal)):
    """Cancelación con penalización escalonada según la antelación. Si la reserva quedó
    pendiente de reasignar por culpa de la empresa, la cancelación es gratuita."""
    reservation = db.get(Reservation, reservation_id)
    if not reservation or (user.role not in STAFF and reservation.customer_id != user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reserva no encontrada")
    if reservation.status not in ("confirmed", "needs_reassignment"):
        raise HTTPException(status.HTTP_409_CONFLICT, f"No se puede cancelar una reserva en estado '{reservation.status}'")

    if reservation.status == "confirmed" and reservation.start_date <= date.today() + timedelta(days=1):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No se puede cancelar durante las 24 horas anteriores al inicio del alquiler.",
        )

    if reservation.status == "needs_reassignment":
        fee, rate = Decimal("0.00"), Decimal("0.00")
    else:
        fee, rate = cancellation_fee(reservation.quoted_total, reservation.start_date, date.today())
    reservation.status = "cancelled"
    reservation.cancellation_fee = fee
    reservation.cancelled_at = datetime.now(timezone.utc)
    db.commit()
    return CancellationOut(
        reservation_id=reservation.id,
        status=reservation.status,
        fee_rate=float(rate),
        cancellation_fee=float(fee),
        refund=float(Decimal(reservation.quoted_total) - fee),
    )


@router.post("/{reservation_id}/reassign", response_model=ReservationOut, dependencies=[Depends(require_roles(*STAFF))])
def reassign_reservation(reservation_id: int, db: Session = Depends(get_db)):
    """Reintento manual de reubicación para reservas en 'needs_reassignment'."""
    reservation = db.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reserva no encontrada")
    if reservation.status != "needs_reassignment":
        raise HTTPException(status.HTTP_409_CONFLICT, "La reserva no está pendiente de reasignación")
    old_category = reservation.vehicle.category
    vehicle = assign_vehicle(db, reservation.start_date, reservation.end_date, old_category)
    if not vehicle:
        raise HTTPException(status.HTTP_409_CONFLICT, "Sigue sin haber vehículos disponibles en esa categoría")
    reservation.vehicle_id = vehicle.id
    reservation.status = "confirmed"
    db.commit()
    db.refresh(reservation)
    return reservation
