from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Vehicle(Base):
    """El estado del vehículo es OPERATIVO: available | maintenance | retired.
    Que esté alquilado se deriva de sus reservas (no se duplica el dato)."""

    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    plate: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    brand: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(50))
    year: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(20), index=True)
    base_daily_rate: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    status: Mapped[str] = mapped_column(String(20), default="available", index=True)
    mileage: Mapped[int] = mapped_column(Integer, default=0)
    branch: Mapped[str] = mapped_column(String(60), default="Málaga")
    seats: Mapped[int] = mapped_column(Integer, default=5)
    transmission: Mapped[str] = mapped_column(String(20), default="manual")
    fuel_type: Mapped[str] = mapped_column(String(20), default="gasolina")
    luggage_capacity: Mapped[int] = mapped_column(Integer, default=2)
    air_conditioning: Mapped[bool] = mapped_column(Boolean, default=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Reservation(Base):
    """customer_id referencia a un usuario de auth-service. No hay FK entre bases de datos:
    la integridad entre servicios se garantiza por API, no por la BD."""

    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, index=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)  # fecha de devolución (exclusiva)
    # confirmed | active | completed | cancelled | needs_reassignment
    status: Mapped[str] = mapped_column(String(25), default="confirmed", index=True)
    extras: Mapped[list] = mapped_column(JSON, default=list)
    quoted_total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    price_breakdown: Mapped[dict] = mapped_column(JSON)
    cancellation_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    vehicle: Mapped[Vehicle] = relationship()


class Rental(Base):
    """Alquiler efectivo: nace en la entrega del vehículo y se cierra en la devolución."""

    __tablename__ = "rentals"

    id: Mapped[int] = mapped_column(primary_key=True)
    reservation_id: Mapped[int] = mapped_column(ForeignKey("reservations.id"), unique=True)
    picked_up_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    start_mileage: Mapped[int] = mapped_column(Integer)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_mileage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    late_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    excess_km_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    damage_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    final_total: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    reservation: Mapped[Reservation] = relationship()


class SeasonRule(Base):
    """Temporada recurrente cada año (mes/día). Admite rangos que cruzan año (20-dic → 6-ene)."""

    __tablename__ = "season_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    start_month: Mapped[int] = mapped_column(Integer)
    start_day: Mapped[int] = mapped_column(Integer)
    end_month: Mapped[int] = mapped_column(Integer)
    end_day: Mapped[int] = mapped_column(Integer)
    multiplier: Mapped[Decimal] = mapped_column(Numeric(4, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
