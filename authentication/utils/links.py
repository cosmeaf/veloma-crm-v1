from typing import Optional
from django.http import HttpRequest
from django.conf import settings

def _host_from_request(request: Optional[HttpRequest]) -> Optional[str]:
    if not request:
        return None
    scheme = request.META.get("HTTP_X_FORWARDED_PROTO") or request.scheme or "https"
    host = request.META.get("HTTP_X_FORWARDED_HOST") or request.get_host()
    if not host:
        return None
    return f"{scheme}://{host}"

def _host_from_settings() -> Optional[str]:
    for key in ("PUBLIC_BASE_URL", "SITE_URL", "FRONTEND_BASE_URL", "BACKEND_BASE_URL"):
        val = getattr(settings, key, None)
        if val:
            return str(val).rstrip("/")
    return None

def absolute(request: Optional[HttpRequest], path: str) -> str:
    base = _host_from_request(request) or _host_from_settings() or "http://127.0.0.1"
    if not path.startswith("/"):
        path = "/" + path
    return f"{base}{path}"

def reset_password_link(request: Optional[HttpRequest], token: str) -> str:
    reset_path = getattr(settings, "AUTH_RESET_PATH", "/reset-password")
    reset_path = reset_path.rstrip("/")
    return absolute(request, f"{reset_path}/{token}")
