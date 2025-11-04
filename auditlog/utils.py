import hashlib
from typing import Any, Dict, Iterable

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def model_to_dict(obj, fields: Iterable[str] | None = None) -> Dict[str, Any]:
    from django.forms.models import model_to_dict as m2d
    try:
        return m2d(obj, fields=list(fields) if fields else None)
    except Exception:
        data = {}
        for f in obj._meta.fields:
            if fields and f.name not in fields:
                continue
            data[f.name] = getattr(obj, f.name)
        return data

def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")

def get_user_agent(request):
    return request.META.get("HTTP_USER_AGENT", "")

def get_groups_snapshot(user):
    return list(user.groups.values_list("name", flat=True)) if user and user.is_authenticated else []
