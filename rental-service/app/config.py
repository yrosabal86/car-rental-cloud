from decimal import Decimal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/rental_db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    internal_api_key: str = "dev-internal-key"
    auth_service_url: str = "http://localhost:8001"
    seed_demo_data: bool = False

    # Reglas de negocio
    max_rental_days: int = 30
    max_active_reservations: int = 3
    included_km_per_day: int = 250
    extra_km_fee: Decimal = Decimal("0.20")  # EUR por km sobre el límite incluido
    late_fee_multiplier: Decimal = Decimal("1.5")  # recargo sobre la tarifa media diaria


settings = Settings()
