"""Motor de tarifas dinámicas. Módulo PURO (sin acceso a BD ni a FastAPI): fácil de testear.

precio_noche = tarifa_base × factor_temporada × factor_fin_de_semana × factor_ocupación
subtotal     = Σ noches
alquiler     = subtotal × max(factor_antelación × factor_larga_estancia, 0.70)
total        = (alquiler + extras) × 1.21 (IVA)
"""
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

TAX_RATE = Decimal("0.21")
WEEKEND_FACTOR = Decimal("1.10")  # noches de viernes y sábado
MIN_COMBINED_DISCOUNT = Decimal("0.70")  # los descuentos nunca superan el 30 %
EXTRAS_PER_DAY = {
    "insurance": Decimal("12.00"),
    "gps": Decimal("5.00"),
    "child_seat": Decimal("4.00"),
}
# (umbral de ocupación de la categoría, factor)
OCCUPANCY_TIERS = ((0.85, Decimal("1.40")), (0.70, Decimal("1.25")), (0.50, Decimal("1.10")))


def money(value) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _rule_matches(rule, day: date) -> bool:
    current = (day.month, day.day)
    start = (rule.start_month, rule.start_day)
    end = (rule.end_month, rule.end_day)
    if start <= end:
        return start <= current <= end
    return current >= start or current <= end  # el rango cruza fin de año


def season_factor(day: date, rules) -> tuple[Decimal, str | None]:
    best, name = Decimal("1.00"), None
    for rule in rules:
        multiplier = Decimal(str(rule.multiplier))
        if _rule_matches(rule, day) and multiplier > best:
            best, name = multiplier, rule.name
    return best, name


def occupancy_factor(utilization: float) -> Decimal:
    for threshold, factor in OCCUPANCY_TIERS:
        if utilization >= threshold:
            return factor
    return Decimal("1.00")


def advance_factor(days_ahead: int) -> tuple[Decimal, str | None]:
    if days_ahead >= 30:
        return Decimal("0.90"), "early_bird_30d"
    if days_ahead >= 14:
        return Decimal("0.95"), "early_bird_14d"
    if days_ahead <= 1:
        return Decimal("1.10"), "last_minute"
    return Decimal("1.00"), None


def long_stay_factor(nights: int) -> tuple[Decimal, str | None]:
    if nights >= 28:
        return Decimal("0.80"), "long_stay_28n"
    if nights >= 14:
        return Decimal("0.85"), "long_stay_14n"
    if nights >= 7:
        return Decimal("0.92"), "long_stay_7n"
    return Decimal("1.00"), None


def calculate_quote(
    *,
    base_rate,
    start: date,
    end: date,
    today: date,
    utilization: dict[date, float],
    rules,
    extras: list[str] | tuple[str, ...] = (),
) -> tuple[Decimal, dict]:
    nights = (end - start).days
    if nights < 1:
        raise ValueError("La reserva debe tener al menos una noche")

    base_rate = Decimal(str(base_rate))
    nightly: list[dict] = []
    subtotal = Decimal("0.00")
    for i in range(nights):
        day = start + timedelta(days=i)
        season, season_name = season_factor(day, rules)
        weekend = WEEKEND_FACTOR if day.weekday() in (4, 5) else Decimal("1.00")
        occupancy = occupancy_factor(utilization.get(day, 0.0))
        price = money(base_rate * season * weekend * occupancy)
        subtotal += price
        nightly.append(
            {
                "date": day.isoformat(),
                "price": float(price),
                "season": season_name,
                "season_factor": float(season),
                "weekend_factor": float(weekend),
                "occupancy": round(utilization.get(day, 0.0), 2),
                "occupancy_factor": float(occupancy),
            }
        )

    adv, adv_label = advance_factor((start - today).days)
    long_, long_label = long_stay_factor(nights)
    combined = max(adv * long_, MIN_COMBINED_DISCOUNT)
    rental_total = money(subtotal * combined)

    extras_detail = {}
    for extra in extras:
        extras_detail[extra] = float(money(EXTRAS_PER_DAY[extra] * nights))
    extras_total = money(sum((Decimal(str(v)) for v in extras_detail.values()), Decimal("0")))

    taxable = rental_total + extras_total
    tax = money(taxable * TAX_RATE)
    total = taxable + tax

    breakdown = {
        "currency": "EUR",
        "nights": nights,
        "base_daily_rate": float(base_rate),
        "nightly": nightly,
        "subtotal_nights": float(subtotal),
        "adjustments": {
            "advance_booking": {"label": adv_label, "factor": float(adv)},
            "long_stay": {"label": long_label, "factor": float(long_)},
            "combined_factor": float(combined),
        },
        "rental_total": float(rental_total),
        "extras": extras_detail,
        "extras_total": float(extras_total),
        "tax_rate": float(TAX_RATE),
        "tax": float(tax),
        "total": float(total),
    }
    return total, breakdown


def cancellation_fee(total: Decimal, start: date, today: date) -> tuple[Decimal, Decimal]:
    """≥7 días: gratis · 3-6 días: 25 % · 24-48 h: 50 % (fechas de calendario)."""
    days_before = (start - today).days
    if days_before >= 7:
        rate = Decimal("0.00")
    elif days_before >= 3:
        rate = Decimal("0.25")
    else:
        rate = Decimal("0.50")
    return money(Decimal(total) * rate), rate
