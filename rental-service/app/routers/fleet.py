from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import STAFF, require_roles
from ..models import Reservation, Vehicle
from ..schemas import (
    Category,
    CategoryUtilization,
    MaintenanceOut,
    VehicleCreate,
    VehicleOut,
    VehicleUpdate,
)
from ..services.availability import BLOCKING_STATUSES
from ..services.fleet_ops import send_to_maintenance

router = APIRouter(prefix="/fleet", tags=["Flota"], dependencies=[Depends(require_roles(*STAFF))])


@router.post("/vehicles", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
def register_vehicle(payload: VehicleCreate, db: Session = Depends(get_db)):
    plate = payload.plate.upper().replace(" ", "")
    if db.scalar(select(Vehicle.id).where(Vehicle.plate == plate)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un vehículo con esa matrícula")
    data = payload.model_dump()
    data["plate"] = plate
    vehicle = Vehicle(**data)
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.put("/vehicles/{vehicle_id}", response_model=VehicleOut)
def update_vehicle(vehicle_id: int, payload: VehicleUpdate, db: Session = Depends(get_db)):
    vehicle = db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehículo no encontrado")
    plate = payload.plate.upper().replace(" ", "")
    duplicate = db.scalar(select(Vehicle.id).where(Vehicle.plate == plate, Vehicle.id != vehicle_id))
    if duplicate:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un vehículo con esa matrícula")
    for key, value in payload.model_dump().items():
        setattr(vehicle, key, value)
    vehicle.plate = plate
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.get("/vehicles", response_model=list[VehicleOut])
def list_vehicles(
    status_: str | None = Query(default=None, alias="status"),
    category: Category | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(Vehicle).order_by(Vehicle.id)
    if status_:
        stmt = stmt.where(Vehicle.status == status_)
    if category:
        stmt = stmt.where(Vehicle.category == category.value)
    return db.scalars(stmt).all()


@router.post("/vehicles/{vehicle_id}/maintenance", response_model=MaintenanceOut)
def send_vehicle_to_maintenance(vehicle_id: int, db: Session = Depends(get_db)):
    """Retira el vehículo de servicio y reubica sus reservas futuras automáticamente."""
    vehicle = db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehículo no encontrado")
    if vehicle.status == "maintenance":
        raise HTTPException(status.HTTP_409_CONFLICT, "El vehículo ya está en mantenimiento")
    in_use = db.scalar(
        select(Reservation.id).where(Reservation.vehicle_id == vehicle_id, Reservation.status == "active")
    )
    if in_use:
        raise HTTPException(status.HTTP_409_CONFLICT, "El vehículo está alquilado ahora mismo")
    result = send_to_maintenance(db, vehicle, date.today())
    db.commit()
    return result


@router.post("/vehicles/{vehicle_id}/activate", response_model=VehicleOut)
def return_vehicle_to_service(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehículo no encontrado")
    if vehicle.status != "maintenance":
        raise HTTPException(status.HTTP_409_CONFLICT, "Solo se puede reactivar un vehículo en mantenimiento")
    vehicle.status = "available"
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.get("/utilization", response_model=list[CategoryUtilization])
def utilization_report(start_date: date, end_date: date, db: Session = Depends(get_db)):
    """KPI de ocupación por categoría = días-vehículo reservados / días-vehículo disponibles."""
    if end_date <= start_date:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "end_date debe ser posterior a start_date")
    days = (end_date - start_date).days
    report = []
    for category in Category:
        fleet = db.scalar(
            select(func.count(Vehicle.id)).where(Vehicle.category == category.value, Vehicle.status == "available")
        ) or 0
        rows = db.execute(
            select(Reservation.start_date, Reservation.end_date)
            .join(Vehicle, Vehicle.id == Reservation.vehicle_id)
            .where(
                Vehicle.category == category.value,
                Reservation.status.in_(BLOCKING_STATUSES + ("completed",)),
                Reservation.start_date < end_date,
                Reservation.end_date > start_date,
            )
        ).all()
        reserved = sum((min(e, end_date) - max(s, start_date)).days for s, e in rows)
        capacity = fleet * days
        report.append(
            CategoryUtilization(
                category=category.value,
                fleet_size=fleet,
                reserved_vehicle_days=reserved,
                capacity_vehicle_days=capacity,
                utilization_pct=round(100 * reserved / capacity, 1) if capacity else 0.0,
            )
        )
    return report
