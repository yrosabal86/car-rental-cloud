from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Category(str, Enum):
    ECONOMY = "economy"
    COMPACT = "compact"
    SUV = "suv"
    PREMIUM = "premium"
    VAN = "van"


class Extra(str, Enum):
    INSURANCE = "insurance"
    GPS = "gps"
    CHILD_SEAT = "child_seat"


class _InSchema(BaseModel):
    model_config = ConfigDict(use_enum_values=True)


class _OutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Flota ----------
class VehicleCreate(_InSchema):
    plate: str = Field(min_length=4, max_length=15)
    brand: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=50)
    year: int = Field(ge=2000, le=2100)
    category: Category
    base_daily_rate: Decimal = Field(gt=0, max_digits=8, decimal_places=2)
    mileage: int = Field(default=0, ge=0)
    branch: str = "Málaga"
    seats: int = Field(default=5, ge=2, le=9)
    transmission: str = Field(default="manual", pattern="^(manual|automatic)$")
    fuel_type: str = Field(default="gasolina", pattern="^(gasolina|diesel|hibrido|electrico)$")
    luggage_capacity: int = Field(default=2, ge=0, le=8)
    air_conditioning: bool = True
    image_url: str | None = Field(default=None, max_length=500)


class VehicleUpdate(_InSchema):
    plate: str = Field(min_length=4, max_length=15)
    brand: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=50)
    year: int = Field(ge=2000, le=2100)
    category: Category
    base_daily_rate: Decimal = Field(gt=0, max_digits=8, decimal_places=2)
    mileage: int = Field(default=0, ge=0)
    branch: str = Field(default="Málaga", max_length=60)
    seats: int = Field(default=5, ge=2, le=9)
    transmission: str = Field(default="manual", pattern="^(manual|automatic)$")
    fuel_type: str = Field(default="gasolina", pattern="^(gasolina|diesel|hibrido|electrico)$")
    luggage_capacity: int = Field(default=2, ge=0, le=8)
    air_conditioning: bool = True
    image_url: str | None = Field(default=None, max_length=500)


class VehicleOut(_OutSchema):
    id: int
    plate: str
    brand: str
    model: str
    year: int
    category: str
    base_daily_rate: float
    status: str
    mileage: int
    branch: str
    seats: int
    transmission: str
    fuel_type: str
    luggage_capacity: int
    air_conditioning: bool
    image_url: str | None


class MaintenanceOut(BaseModel):
    vehicle_id: int
    status: str
    reassigned: list[dict]
    needs_reassignment: list[int]


class CategoryUtilization(BaseModel):
    category: str
    fleet_size: int
    reserved_vehicle_days: int
    capacity_vehicle_days: int
    utilization_pct: float


# ---------- Tarifas y disponibilidad ----------
class QuoteRequest(_InSchema):
    category: Category
    start_date: date
    end_date: date
    extras: list[Extra] = []


class QuoteOut(BaseModel):
    category: str
    nights: int
    total: float
    breakdown: dict


class AvailableVehicleOut(BaseModel):
    vehicle: VehicleOut
    nights: int
    total: float
    avg_per_night: float


class SeasonRuleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    start_month: int = Field(ge=1, le=12)
    start_day: int = Field(ge=1, le=31)
    end_month: int = Field(ge=1, le=12)
    end_day: int = Field(ge=1, le=31)
    multiplier: Decimal = Field(ge=Decimal("0.5"), le=Decimal("3.0"), max_digits=4, decimal_places=2)


class SeasonRuleOut(_OutSchema):
    id: int
    name: str
    start_month: int
    start_day: int
    end_month: int
    end_day: int
    multiplier: float
    is_active: bool


# ---------- Reservas ----------
class ReservationCreate(_InSchema):
    start_date: date
    end_date: date
    category: Category | None = None
    vehicle_id: int | None = None
    extras: list[Extra] = []

    @model_validator(mode="after")
    def need_category_or_vehicle(self):
        if self.category is None and self.vehicle_id is None:
            raise ValueError("Indica 'category' (asignación automática) o 'vehicle_id'")
        return self


class ReservationOut(_OutSchema):
    id: int
    customer_id: int
    vehicle_id: int
    start_date: date
    end_date: date
    status: str
    extras: list[str]
    quoted_total: float
    price_breakdown: dict
    cancellation_fee: float
    created_at: datetime
    cancelled_at: datetime | None


class CancellationOut(BaseModel):
    reservation_id: int
    status: str
    fee_rate: float
    cancellation_fee: float
    refund: float


# ---------- Alquileres ----------
class PickupRequest(BaseModel):
    reservation_id: int
    notes: str | None = None


class ReturnRequest(BaseModel):
    end_mileage: int = Field(ge=0)
    damage_fee: Decimal = Field(default=Decimal("0"), ge=0, max_digits=8, decimal_places=2)
    requires_maintenance: bool = False
    notes: str | None = None


class RentalOut(_OutSchema):
    id: int
    reservation_id: int
    picked_up_at: datetime
    start_mileage: int
    returned_at: datetime | None
    end_mileage: int | None
    late_fee: float
    excess_km_fee: float
    damage_fee: float
    final_total: float | None
    notes: str | None
