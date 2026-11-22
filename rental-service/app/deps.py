from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

bearer_scheme = HTTPBearer()
STAFF = ("admin", "fleet_manager")


@dataclass(frozen=True)
class Principal:
    id: int
    email: str
    role: str


def get_principal(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> Principal:
    """Valida el JWT localmente (secreto compartido): no hace falta llamar a auth-service
    en cada petición, lo que reduce latencia y acoplamiento."""
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        raise unauthorized
    if payload.get("type") != "access" or "sub" not in payload or "role" not in payload:
        raise unauthorized
    return Principal(id=int(payload["sub"]), email=payload.get("email", ""), role=payload["role"])


def require_roles(*roles: str):
    def checker(principal: Principal = Depends(get_principal)) -> Principal:
        if principal.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No tienes permisos para esta operación")
        return principal

    return checker
