"""Cliente síncrono REST hacia auth-service (comunicación servicio-a-servicio)."""
import httpx

from .config import settings


class AuthServiceUnavailable(Exception):
    pass


def fetch_user(user_id: int) -> dict | None:
    """Devuelve el perfil del usuario, None si no existe. Lanza AuthServiceUnavailable
    si auth-service no responde (el llamante decide cómo degradar: aquí, fail-fast 503)."""
    url = f"{settings.auth_service_url}/internal/users/{user_id}"
    headers = {"X-Internal-Api-Key": settings.internal_api_key}
    last_error: Exception | None = None
    for _ in range(2):  # 1 reintento ante fallos transitorios
        try:
            response = httpx.get(url, headers=headers, timeout=3.0)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            last_error = exc
    raise AuthServiceUnavailable(str(last_error))
