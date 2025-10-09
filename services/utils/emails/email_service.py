from typing import Dict, Any, Optional, Sequence, Tuple
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_email_task(
    self,
    subject: str,
    to_email: Sequence[str],
    text_body: str,
    html_body: Optional[str] = None,
    from_email: Optional[str] = None,
    cc: Optional[Sequence[str]] = None,
    bcc: Optional[Sequence[str]] = None,
    attachments: Optional[Sequence[Tuple[str, bytes, str]]] = None,
):
    """
    Tarefa Celery para envio de e-mail real.
    - Reenvia até 3x em caso de falha.
    """
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body or "",
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            to=to_email,
            cc=cc or [],
            bcc=bcc or [],
        )

        if html_body:
            msg.attach_alternative(html_body, "text/html")

        if attachments:
            for name, content, mimetype in attachments:
                msg.attach(name, content, mimetype)

        sent_count = msg.send(fail_silently=False)
        logger.info("E-mail enviado: %s -> %s (count=%s)", subject, to_email, sent_count)

    except Exception as exc:
        logger.error("Erro ao enviar e-mail '%s' para %s: %s", subject, to_email, exc)
        raise self.retry(exc=exc, countdown=60)  # tenta novamente em 60s


class EmailService:
    """
    Serviço de envio de e-mails via Celery.
    Uso:
        EmailService(
            subject="Assunto",
            to_email="user@example.com",
            template_name="emails/welcome",
            context={"user": "Alex"}
        ).send()
    """

    def __init__(
        self,
        subject: str,
        to_email: Sequence[str] | str,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
        from_email: Optional[str] = None,
        cc: Optional[Sequence[str]] = None,
        bcc: Optional[Sequence[str]] = None,
        attachments: Optional[Sequence[Tuple[str, bytes, str]]] = None,
    ):
        if not subject:
            raise ValueError("O campo 'subject' é obrigatório.")
        if not to_email:
            raise ValueError("O campo 'to_email' é obrigatório.")
        if not template_name:
            raise ValueError("O campo 'template_name' é obrigatório.")

        self.subject = str(subject).strip()
        self.to_email = to_email if isinstance(to_email, list) else [to_email]
        self.template_name = template_name
        self.context = self._prepare_context(context or {})
        self.from_email = from_email or settings.DEFAULT_FROM_EMAIL
        self.cc = cc or []
        self.bcc = bcc or []
        self.attachments = attachments or []

    def _prepare_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Garante que o contexto seja serializável (necessário para Celery).
        """
        safe = {}
        for key, value in context.items():
            try:
                safe[key] = str(value) if hasattr(value, "__dict__") else value
            except Exception as e:
                logger.warning("Erro ao serializar campo %s: %s", key, e)
                safe[key] = str(value)
        return safe

    def _render_bodies(self) -> tuple[str, Optional[str]]:
        """
        Renderiza templates TXT e HTML.
        Exemplo: "emails/password_recovery" procura:
          - templates/emails/password_recovery.txt
          - templates/emails/password_recovery.html
        """
        text_body = ""
        html_body = None

        try:
            text_body = render_to_string(f"{self.template_name}.txt", self.context)
        except Exception:
            logger.debug("Template TXT não encontrado: %s.txt", self.template_name)

        try:
            html_body = render_to_string(f"{self.template_name}.html", self.context)
        except Exception:
            logger.debug("Template HTML não encontrado: %s.html", self.template_name)

        if not text_body and html_body:
            text_body = strip_tags(html_body)

        if not text_body:
            raise ValueError(f"Template {self.template_name} não contém conteúdo válido.")

        return text_body.strip(), html_body

    def send(self) -> None:
        """
        Agenda o envio do e-mail em background via Celery.
        """
        text_body, html_body = self._render_bodies()

        send_email_task.delay(
            subject=self.subject,
            to_email=self.to_email,
            text_body=text_body,
            html_body=html_body,
            from_email=self.from_email,
            cc=self.cc,
            bcc=self.bcc,
            attachments=self.attachments,
        )

        logger.info("Agendado envio de e-mail '%s' para %s", self.subject, self.to_email)
