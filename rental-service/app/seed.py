from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import SeasonRule, Vehicle

DEFAULT_SEASONS = [
    ("Navidad y Año Nuevo", 12, 20, 1, 6, "1.25"),
    ("Verano medio", 6, 15, 6, 30, "1.10"),
    ("Verano alto", 7, 1, 8, 31, "1.30"),
]


def seed_season_rules(db: Session) -> None:
    if db.scalar(select(SeasonRule.id).limit(1)):
        return
    for name, sm, sd, em, ed, mult in DEFAULT_SEASONS:
        db.add(SeasonRule(name=name, start_month=sm, start_day=sd, end_month=em, end_day=ed, multiplier=mult))
    db.commit()


DEMO_VEHICLES = [
    ("4821KLM", "SEAT", "Ibiza", 2024, "economy", "35.00", 12400, "Málaga"),
    ("7314LNP", "Toyota", "Yaris", 2024, "economy", "38.00", 8200, "Málaga"),
    ("1938MPR", "Volkswagen", "Golf", 2023, "compact", "49.00", 21700, "Málaga"),
    ("5502NTS", "Peugeot", "3008", 2024, "suv", "72.00", 10800, "Málaga"),
    ("8641PKV", "Volvo", "XC40", 2025, "premium", "105.00", 3200, "Málaga"),
    ("2067RWL", "Ford", "Tourneo Connect", 2023, "van", "88.00", 28400, "Málaga"),
]

DEMO_FEATURES = {
    ("SEAT", "Ibiza"): {"seats": 5, "transmission": "manual", "fuel_type": "gasolina", "luggage_capacity": 2},
    ("Toyota", "Yaris"): {"seats": 5, "transmission": "automatic", "fuel_type": "hibrido", "luggage_capacity": 2},
    ("Volkswagen", "Golf"): {"seats": 5, "transmission": "automatic", "fuel_type": "gasolina", "luggage_capacity": 3},
    ("Peugeot", "3008"): {"seats": 5, "transmission": "automatic", "fuel_type": "hibrido", "luggage_capacity": 3},
    ("Volvo", "XC40"): {"seats": 5, "transmission": "automatic", "fuel_type": "hibrido", "luggage_capacity": 3},
    ("Ford", "Tourneo Connect"): {"seats": 7, "transmission": "manual", "fuel_type": "diesel", "luggage_capacity": 5},
}


def seed_demo_vehicles(db: Session) -> None:
    """Carga una flota de muestra solo cuando el entorno local lo solicita."""
    if db.scalar(select(Vehicle.id).limit(1)):
        return
    db.add_all(
        [
            Vehicle(
                plate=plate,
                brand=brand,
                model=model,
                year=year,
                category=category,
                base_daily_rate=rate,
                mileage=mileage,
                branch=branch,
                **DEMO_FEATURES[(brand, model)],
            )
            for plate, brand, model, year, category, rate, mileage, branch in DEMO_VEHICLES
        ]
    )
    db.commit()
