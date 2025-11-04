import uuid
from django.utils.deprecation import MiddlewareMixin
from .models import AuditEvent
from .utils import get_client_ip, get_user_agent, sha256_text

_REQUEST_ID_HEADER = "HTTP_X_REQUEST_ID"
_REQUEST_ID_ATTR = "request_id"

class RequestIDMiddleware(MiddlewareMixin):
    def process_request(self, request):
        rid = request.META.get(_REQUEST_ID_HEADER) or uuid.uuid4().hex
        setattr(request, _REQUEST_ID_ATTR, rid)

class AuditMiddleware(MiddlewareMixin):
    """
    Registra eventos de ACESSO (GET/HEAD) e também captura payload_hash
    para POST/PUT/PATCH/DELETE (sem armazenar o corpo).
    Use signals para CREATE/UPDATE/DELETE detalhados por objeto.
    """
    def process_request(self, request):
        request._audit_body = b""
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            try:
                request._audit_body = request.body or b""
            except Exception:
                request._audit_body = b""

    def process_response(self, request, response):
        try:
            # Registra acesso só para métodos seguros; para write, os signals geram eventos.
            if request.method in ("GET", "HEAD", "OPTIONS"):
                AuditEvent.objects.create(
                    user=getattr(request, "user", None) if getattr(request, "user", None).is_authenticated else None,
                    user_repr=getattr(request, "user", None).email if getattr(request, "user", None) and getattr(request, "user", None).is_authenticated else None,
                    user_is_staff=getattr(request, "user", None).is_staff if getattr(request, "user", None) else False,
                    user_is_superuser=getattr(request, "user", None).is_superuser if getattr(request, "user", None) else False,
                    user_groups=[],
                    method=request.method,
                    path=request.get_full_path()[:512],
                    status_code=response.status_code,
                    ip=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    request_id=getattr(request, "request_id", None),
                    action=AuditEvent.Action.ACCESS,
                )
            else:
                # grava apenas hash do payload para correlação
                body = getattr(request, "_audit_body", b"") or b""
                AuditEvent.objects.create(
                    user=getattr(request, "user", None) if getattr(request, "user", None).is_authenticated else None,
                    user_repr=getattr(request, "user", None).email if getattr(request, "user", None) and getattr(request, "user", None).is_authenticated else None,
                    user_is_staff=getattr(request, "user", None).is_staff if getattr(request, "user", None) else False,
                    user_is_superuser=getattr(request, "user", None).is_superuser if getattr(request, "user", None) else False,
                    user_groups=[],
                    method=request.method,
                    path=request.get_full_path()[:512],
                    status_code=response.status_code,
                    ip=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    request_id=getattr(request, "request_id", None),
                    action=AuditEvent.Action.OTHER,
                    payload_hash=sha256_text(body.decode("utf-8", errors="ignore")) if body else None,
                )
        except Exception:
            pass
        return response
