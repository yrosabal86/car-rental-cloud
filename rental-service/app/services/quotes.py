from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import SeasonRule
from .availability import utilization_by_day
from .pricing import calculate_quote


def load_rules(db: Session) -> list[SeasonRule]:
    return list(db.scalars(select(SeasonRule).where(SeasonRule.is_active)))


def build_quote(
    db: Session,
    *,
    category: str,
    base_rate,
    start: date,
    end: date,
    extras: list[str],
    utilization: dict | None = None,
    rules: list | None = None,
) -> tuple[Decimal, dict]:
    return calculate_quote(
        base_rate=base_rate,
        start=start,
        end=end,
        today=date.today(),
        utilization=utilization if utilization is not None else utilization_by_day(db, category, start, end),
        rules=rules if rules is not None else load_rules(db),
        extras=extras,
    )
