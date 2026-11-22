from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/auth_db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    internal_api_key: str = "dev-internal-key"

    max_failed_attempts: int = 5
    lock_minutes: int = 15
    min_customer_age: int = 21

    bootstrap_admin_email: str = "admin@carrental.local"
    bootstrap_admin_password: str = "Admin1234!"


settings = Settings()
