from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import STAFF, Principal, get_principal, require_roles
from ..models import Rental, Reservation
from ..schemas import PickupRequest, RentalOut, ReturnRequest
from ..services.fleet_ops import send_to_maintenance
from ..services.pricing import money

router = APIRouter(prefix="/rentals", tags=["Alquileres"])


@router.post(
    "/pickup",
    response_model=RentalOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*STAFF))],
)
def pickup_vehicle(payload: PickupRequest, db: Session = Depends(get_db)):
    """Entrega del vehículo: convierte la reserva en un alquiler activo."""
    reservation = db.get(Reservation, payload.reservation_id)
    if not reservation:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reserva no encontrada")
    if reservation.status != "confirmed":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Reserva en estado '{reservation.status}', no se puede entregar")

    today = date.today()
    if today < reservation.start_date:
        raise HTTPException(status.HTTP_409_CONFLICT, "Aún no ha llegado la fecha de inicio de la reserva")
    if today >= reservation.end_date:
        raise HTTPException(status.HTTP_409_CONFLICT, "La reserva ya ha expirado")

    vehicle = reservation.vehicle
    if vehicle.status != "available":
        raise HTTPException(status.HTTP_409_CONFLICT, "El vehículo no está operativo")
    still_out = db.scalar(
        select(Reservation.id).where(Reservation.vehicle_id == vehicle.id, Reservation.status == "active")
    )
    if still_out:
        raise HTTPException(status.HTTP_409_CONFLICT, "El vehículo aún no ha sido devuelto por el cliente anterior")

    rental = Rental(reservation_id=reservation.id, start_mileage=vehicle.mileage, notes=payload.notes)
    reservation.status = "active"
    db.add(rental)
    db.commit()
    db.refresh(rental)
    return rental


@router.post("/{rental_id}/return", response_model=RentalOut, dependencies=[Depends(require_roles(*STAFF))])
def return_vehicle(rental_id: int, payload: ReturnRequest, db: Session = Depends(get_db)):
    """Devolución: calcula recargos por retraso, kilometraje excedido y daños, y cierra el alquiler."""
    rental = db.get(Rental, rental_id)
    if not rental:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alquiler no encontrado")
    if rental.returned_at:
        raise HTTPException(status.HTTP_409_CONFLICT, "El alquiler ya fue cerrado")
    if payload.end_mileage < rental.start_mileage:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El kilometraje final no puede ser inferior al inicial")

    reservation = rental.reservation
    vehicle = reservation.vehicle
    now = datetime.now(UTC)
    today = now.date()

    nights = (reservation.end_date - reservation.start_date).days
    quoted = Decimal(reservation.quoted_total)
    avg_night = quoted / nights

    late_days = max(0, (today - reservation.end_date).days)
    late_fee = money(avg_night * late_days * settings.late_fee_multiplier)

    km_driven = payload.end_mileage - rental.start_mileage
    excess_km = max(0, km_driven - settings.included_km_per_day * nights)
    excess_fee = money(Decimal(excess_km) * settings.extra_km_fee)

    damage_fee = money(payload.damage_fee)

    rental.returned_at = now
    rental.end_mileage = payload.end_mileage
    rental.late_fee = late_fee
    rental.excess_km_fee = excess_fee
    rental.damage_fee = damage_fee
    rental.final_total = money(quoted + late_fee + excess_fee + damage_fee)
    if payload.notes:
        rental.notes = f"{rental.notes}\n{payload.notes}" if rental.notes else payload.notes

    reservation.status = "completed"
    vehicle.mileage = payload.end_mileage
    db.flush()

    # Si hay daños, el vehículo sale de servicio y se reubican las reservas futuras
    if payload.requires_maintenance or damage_fee > 0:
        send_to_maintenance(db, vehicle, today)

    db.commit()
    db.refresh(rental)
    return rental


@router.get("/{rental_id}", response_model=RentalOut)
def get_rental(rental_id: int, db: Session = Depends(get_db), user: Principal = Depends(get_principal)):
    rental = db.get(Rental, rental_id)
    if not rental or (user.role not in STAFF and rental.reservation.customer_id != user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alquiler no encontrado")
    return rental


@router.get("", response_model=list[RentalOut], dependencies=[Depends(require_roles(*STAFF))])
def list_rentals(db: Session = Depends(get_db)):
    return db.scalars(select(Rental).order_by(Rental.picked_up_at.desc())).all()
