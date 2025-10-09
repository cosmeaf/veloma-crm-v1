# authentication/utils/email_events.py
from typing import Optional, Dict, Any
from django.http import HttpRequest
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

from services.utils.emails.sendemail import EmailService
from .links import absolute, reset_password_link

logger = logging.getLogger(__name__)
User = get_user_model()

def _svc(tenant_office_id: Optional[int] = None) -> EmailService:
    # Se um dia amarrar provider por tenant/office, passe office_id aqui.
    return EmailService(theme="default", tenant_office_id=tenant_office_id)

def send_welcome(user: User, extra_ctx: Optional[Dict[str, Any]] = None) -> str:
    ctx = {"user": user, **(extra_ctx or {})}
    try:
        return _svc().send_by_template(
            template_code="welcome",
            to=[user.email],
            context=ctx,
            # subject="Bem-vindo(a) à Veloma",  # opcional, se quiser fixar
        )
    except Exception as e:
        logger.exception("Falha ao enviar e-mail de boas-vindas: %s", e)
        raise

def send_password_recovery(user: User, otp_code: str) -> str:
    ctx = {"user": user, "otp_code": otp_code}
    try:
        return _svc().send_by_template(
            template_code="password_recovery",
            to=[user.email],
            context=ctx,
            # subject="Código de recuperação",  # opcional (se o template subject não existir)
        )
    except Exception as e:
        logger.exception("Falha ao enviar e-mail de recuperação: %s", e)
        raise

def send_password_changed(user: User) -> str:
    ctx = {"user": user, "changed_at": timezone.now()}
    try:
        return _svc().send_by_template(
            template_code="password_changed",
            to=[user.email],
            context=ctx,
        )
    except Exception as e:
        logger.exception("Falha ao enviar e-mail de confirmação de alteração de senha: %s", e)
        raise

def verification_link(request: Optional[HttpRequest], token: str) -> str:
    verify_path = "/verify-email"  # pode ajustar via settings se quiser
    return absolute(request, f"{verify_path.rstrip('/')}/{token}")

def send_verify_email(user: User, request: Optional[HttpRequest], token: str) -> str:
    link = verification_link(request, token)
    ctx = {"user": user, "verify_link": link}
    try:
        return _svc().send_by_template(
            template_code="email_verify",
            to=[user.email],
            context=ctx,
        )
    except Exception as e:
        logger.exception("Falha ao enviar e-mail de verificação: %s", e)
        raise

def send_login_alert(user: User, request: Optional[HttpRequest]) -> str:
    ip = None
    if request:
        fwd = request.META.get("HTTP_X_FORWARDED_FOR", "")
        ip = fwd.split(",")[0].strip() if fwd else request.META.get("REMOTE_ADDR")
    ua = request.META.get("HTTP_USER_AGENT") if request else None
    ctx = {"user": user, "ip": ip, "user_agent": ua, "when": timezone.now()}
    try:
        return _svc().send_by_template(
            template_code="login_alert",
            to=[user.email],
            context=ctx,
        )
    except Exception as e:
        logger.exception("Falha ao enviar alerta de login: %s", e)
        raise
