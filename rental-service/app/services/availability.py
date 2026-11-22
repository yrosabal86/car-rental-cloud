from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Reservation, Vehicle

BLOCKING_STATUSES = ("confirmed", "active")


def _overlap(start: date, end: date):
    """Dos rangos [inicio, fin) se solapan si inicio_a < fin_b y fin_a > inicio_b."""
    return (
        Reservation.status.in_(BLOCKING_STATUSES),
        Reservation.start_date < end,
        Reservation.end_date > start,
    )


def has_overlap(db: Session, vehicle_id: int, start: date, end: date) -> bool:
    stmt = select(Reservation.id).where(Reservation.vehicle_id == vehicle_id, *_overlap(start, end)).limit(1)
    return db.scalar(stmt) is not None


def available_vehicles(
    db: Session,
    start: date,
    end: date,
    category: str | None = None,
    exclude_id: int | None = None,
) -> list[Vehicle]:
    busy = select(Reservation.vehicle_id).where(*_overlap(start, end))
    stmt = select(Vehicle).where(Vehicle.status == "available", Vehicle.id.not_in(busy))
    if category:
        stmt = stmt.where(Vehicle.category == category)
    if exclude_id:
        stmt = stmt.where(Vehicle.id != exclude_id)
    # Rotación de flota: primero los de menor kilometraje
    return list(db.scalars(stmt.order_by(Vehicle.mileage.asc(), Vehicle.id.asc())))


def assign_vehicle(
    db: Session,
    start: date,
    end: date,
    category: str,
    vehicle_id: int | None = None,
    exclude_id: int | None = None,
) -> Vehicle | None:
    """Asigna un vehículo libre bloqueando su fila (SELECT ... FOR UPDATE) y revalidando,
    para evitar dobles reservas con peticiones concurrentes."""
    candidates = available_vehicles(db, start, end, category, exclude_id)
    if vehicle_id is not None:
        candidates = [v for v in candidates if v.id == vehicle_id]
    for candidate in candidates:
        locked = db.scalar(select(Vehicle).where(Vehicle.id == candidate.id).with_for_update())
        if locked and locked.status == "available" and not has_overlap(db, locked.id, start, end):
            return locked
    return None


def utilization_by_day(db: Session, category: str, start: date, end: date) -> dict[date, float]:
    """Ocupación diaria de una categoría (0.0-1.0): alimenta el factor de demanda."""
    fleet = db.scalar(
        select(func.count(Vehicle.id)).where(Vehicle.category == category, Vehicle.status == "available")
    ) or 0
    days = [start + timedelta(days=i) for i in range((end - start).days)]
    if fleet == 0:
        return {d: 1.0 for d in days}  # sin flota operativa = máxima escasez
    rows = db.execute(
        select(Reservation.start_date, Reservation.end_date)
        .join(Vehicle, Vehicle.id == Reservation.vehicle_id)
        .where(Vehicle.category == category, *_overlap(start, end))
    ).all()
    return {d: min(1.0, sum(1 for s, e in rows if s <= d < e) / fleet) for d in days}
