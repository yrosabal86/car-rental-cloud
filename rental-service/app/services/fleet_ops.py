from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Reservation, Vehicle
from .availability import assign_vehicle


def send_to_maintenance(db: Session, vehicle: Vehicle, today: date) -> dict:
    """Retira un vehículo y reubica automáticamente sus reservas futuras en otro vehículo
    libre de la misma categoría, respetando el precio ya acordado con el cliente.
    Las que no tengan alternativa pasan a 'needs_reassignment' para gestión manual."""
    vehicle.status = "maintenance"
    db.flush()

    affected = db.scalars(
        select(Reservation)
        .where(
            Reservation.vehicle_id == vehicle.id,
            Reservation.status == "confirmed",
            Reservation.end_date > today,
        )
        .order_by(Reservation.start_date)
    ).all()

    reassigned, unresolved = [], []
    for reservation in affected:
        alternative = assign_vehicle(
            db, reservation.start_date, reservation.end_date, vehicle.category, exclude_id=vehicle.id
        )
        if alternative:
            reservation.vehicle_id = alternative.id
            db.flush()
            reassigned.append({"reservation_id": reservation.id, "new_vehicle_id": alternative.id})
        else:
            reservation.status = "needs_reassignment"
            unresolved.append(reservation.id)

    return {
        "vehicle_id": vehicle.id,
        "status": vehicle.status,
        "reassigned": reassigned,
        "needs_reassignment": unresolved,
    }
