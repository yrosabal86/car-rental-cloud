from contextlib import asynccontextmanager
from sqlalchemy import text

from fastapi import FastAPI

from .database import SessionLocal, init_db
from .routers import fleet, pricing, rentals, reservations
from .config import settings
from .seed import seed_demo_vehicles, seed_season_rules

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # create_all no altera tablas existentes; añade el nuevo campo de imagen a instalaciones previas.
    from .database import engine
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS image_url VARCHAR(500)"))
    with SessionLocal() as db:
        seed_season_rules(db)
        if settings.seed_demo_data:
            seed_demo_vehicles(db)
    yield


app = FastAPI(
    title="Car Rental - rental-service",
    description="Flota, tarifas dinámicas, motor de reservas y procesamiento de alquileres.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(pricing.router)
app.include_router(fleet.router)
app.include_router(reservations.router)
app.include_router(rentals.router)


@app.get("/health", tags=["Health"])
def health():
    return {"service": "rental-service", "status": "ok"}
