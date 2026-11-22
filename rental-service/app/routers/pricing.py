from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import require_roles
from ..models import SeasonRule, Vehicle
from ..schemas import (
    AvailableVehicleOut,
    Category,
    QuoteOut,
    QuoteRequest,
    SeasonRuleCreate,
    SeasonRuleOut,
    VehicleOut,
)
from ..services.availability import available_vehicles, utilization_by_day
from ..services.pricing import calculate_quote
from ..services.quotes import build_quote, load_rules

router = APIRouter(tags=["Tarifas y disponibilidad"])


def validate_dates(start: date, end: date) -> None:
    if start < date.today():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "start_date no puede estar en el pasado")
    if end <= start:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "end_date debe ser posterior a start_date")
    if (end - start).days > settings.max_rental_days:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"La duración máxima de un alquiler es {settings.max_rental_days} días",
        )


@router.post("/pricing/quote", response_model=QuoteOut)
def quote(payload: QuoteRequest, db: Session = Depends(get_db)):
    """Presupuesto dinámico por categoría (tarifa media de la flota operativa)."""
    validate_dates(payload.start_date, payload.end_date)
    avg_rate = db.scalar(
        select(func.avg(Vehicle.base_daily_rate)).where(
            Vehicle.category == payload.category, Vehicle.status == "available"
        )
    )
    if avg_rate is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No hay vehículos operativos en esa categoría")
    total, breakdown = build_quote(
        db,
        category=payload.category,
        base_rate=avg_rate,
        start=payload.start_date,
        end=payload.end_date,
        extras=payload.extras,
    )
    return QuoteOut(
        category=payload.category, nights=breakdown["nights"], total=float(total), breakdown=breakdown
    )


@router.get("/availability", response_model=list[AvailableVehicleOut])
def search_availability(
    start_date: date,
    end_date: date,
    category: Category | None = None,
    db: Session = Depends(get_db),
):
    """Vehículos libres en el rango, cada uno con su precio dinámico calculado."""
    validate_dates(start_date, end_date)
    vehicles = available_vehicles(db, start_date, end_date, category.value if category else None)
    rules = load_rules(db)
    util_cache: dict[str, dict] = {}
    results = []
    for v in vehicles:
        util = util_cache.setdefault(v.category, utilization_by_day(db, v.category, start_date, end_date))
        total, breakdown = calculate_quote(
            base_rate=v.base_daily_rate,
            start=start_date,
            end=end_date,
            today=date.today(),
            utilization=util,
            rules=rules,
        )
        nights = breakdown["nights"]
        results.append(
            AvailableVehicleOut(
                vehicle=VehicleOut.model_validate(v),
                nights=nights,
                total=float(total),
                avg_per_night=round(float(total) / nights, 2),
            )
        )
    return sorted(results, key=lambda r: r.total)


@router.get("/pricing/season-rules", response_model=list[SeasonRuleOut])
def list_season_rules(db: Session = Depends(get_db)):
    return db.scalars(select(SeasonRule).order_by(SeasonRule.id)).all()


@router.post(
    "/pricing/season-rules",
    response_model=SeasonRuleOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("admin"))],
)
def create_season_rule(payload: SeasonRuleCreate, db: Session = Depends(get_db)):
    rule = SeasonRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete(
    "/pricing/season-rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("admin"))],
)
def delete_season_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(SeasonRule, rule_id)
    if not rule:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Regla no encontrada")
    db.delete(rule)
    db.commit()
