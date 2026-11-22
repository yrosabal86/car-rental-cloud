import time

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(retries: int = 15, delay: float = 2.0) -> None:
    from . import models  # noqa: F401

    for attempt in range(1, retries + 1):
        try:
            has_vehicle_table = inspect(engine).has_table("vehicles")
            has_feature_columns = has_vehicle_table and "seats" in {
                column["name"] for column in inspect(engine).get_columns("vehicles")
            }
            Base.metadata.create_all(bind=engine)
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS seats INTEGER NOT NULL DEFAULT 5"))
                connection.execute(text("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS transmission VARCHAR(20) NOT NULL DEFAULT 'manual'"))
                connection.execute(text("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS fuel_type VARCHAR(20) NOT NULL DEFAULT 'gasolina'"))
                connection.execute(text("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS luggage_capacity INTEGER NOT NULL DEFAULT 2"))
                connection.execute(text("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS air_conditioning BOOLEAN NOT NULL DEFAULT TRUE"))
                if not has_feature_columns:
                    connection.execute(text("UPDATE vehicles SET seats = CASE category WHEN 'van' THEN 7 ELSE 5 END, luggage_capacity = CASE category WHEN 'economy' THEN 2 WHEN 'van' THEN 5 ELSE 3 END"))
                    connection.execute(text("UPDATE vehicles SET transmission = 'automatic', fuel_type = 'hibrido' WHERE brand = 'Toyota' AND model = 'Yaris'"))
                    connection.execute(text("UPDATE vehicles SET fuel_type = 'diesel' WHERE brand = 'Ford' AND model = 'Tourneo Connect'"))
                    connection.execute(text("UPDATE vehicles SET transmission = 'automatic' WHERE (brand = 'Volkswagen' AND model = 'Golf') OR (brand = 'Peugeot' AND model = '3008') OR (brand = 'Volvo' AND model = 'XC40')"))
                    connection.execute(text("UPDATE vehicles SET fuel_type = 'hibrido' WHERE (brand = 'Peugeot' AND model = '3008') OR (brand = 'Volvo' AND model = 'XC40')"))
                    connection.execute(text("UPDATE vehicles SET seats = 7, luggage_capacity = 5 WHERE brand = 'Ford' AND model = 'Tourneo Connect'"))
            return
        except OperationalError:
            if attempt == retries:
                raise
            time.sleep(delay)
