from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .models import User
from .security import hash_password


def ensure_admin(db: Session) -> None:
    """Crea el primer administrador si no existe ninguno (arranque en frío)."""
    exists = db.scalar(select(User.id).where(User.role == "admin").limit(1))
    if exists:
        return
    db.add(
        User(
            email=settings.bootstrap_admin_email.lower(),
            full_name="Administrador",
            password_hash=hash_password(settings.bootstrap_admin_password),
            role="admin",
        )
    )
    db.commit()
