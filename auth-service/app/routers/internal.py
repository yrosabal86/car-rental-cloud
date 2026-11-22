from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import verify_internal_key
from ..models import User
from ..schemas import InternalUserOut

router = APIRouter(
    prefix="/internal",
    tags=["Interno (servicio a servicio)"],
    dependencies=[Depends(verify_internal_key)],
)


@router.get("/users/{user_id}", response_model=InternalUserOut)
def get_user_for_service(user_id: int, db: Session = Depends(get_db)):
    """Usado por rental-service para comprobar que el cliente existe y está activo."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    return user
