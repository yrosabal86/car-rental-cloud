from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_roles
from ..models import User
from ..schemas import RoleUpdate, StaffCreateRequest, StatusUpdate, UserOut
from ..security import hash_password

router = APIRouter(prefix="/admin", tags=["Administración de usuarios"])
admin_only = Depends(require_roles("admin"))


@router.get("/users", response_model=list[UserOut], dependencies=[admin_only])
def list_users(role: str | None = None, is_active: bool | None = None, db: Session = Depends(get_db)):
    stmt = select(User).order_by(User.id)
    if role:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    return db.scalars(stmt).all()


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED, dependencies=[admin_only])
def create_staff_user(payload: StaffCreateRequest, db: Session = Depends(get_db)):
    """Alta de personal (administradores y gestores de flota)."""
    email = payload.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un usuario con ese email")
    user = User(
        email=email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/role", response_model=UserOut)
def change_role(
    user_id: int,
    payload: RoleUpdate,
    current: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    if user.id == current.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "No puedes cambiar tu propio rol")
    if user.role == "admin" and payload.role.value != "admin":
        admins = db.scalar(select(func.count(User.id)).where(User.role == "admin", User.is_active))
        if admins <= 1:
            raise HTTPException(status.HTTP_409_CONFLICT, "Debe quedar al menos un administrador activo")
    user.role = payload.role.value
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/status", response_model=UserOut)
def change_status(
    user_id: int,
    payload: StatusUpdate,
    current: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    if user.id == current.id and not payload.is_active:
        raise HTTPException(status.HTTP_409_CONFLICT, "No puedes desactivarte a ti mismo")
    user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return user
