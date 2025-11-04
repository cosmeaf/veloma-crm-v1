from django.db import models
from django.conf import settings

class AuditEvent(models.Model):
    class Action(models.TextChoices):
        CREATE = "create"
        UPDATE = "update"
        DELETE = "delete"
        LOGIN  = "login"
        LOGOUT = "logout"
        ACCESS = "access"   # leitura/GET ou ação genérica
        OTHER  = "other"

    # quem
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_events")
    user_repr = models.CharField(max_length=200, blank=True, null=True)     # snapshot (email/NIF)
    user_is_staff = models.BooleanField(default=False)
    user_is_superuser = models.BooleanField(default=False)
    user_groups = models.JSONField(default=list, blank=True)                # ["staff","client"]

    # contexto
    occurred_at = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    request_id = models.CharField(max_length=64, blank=True, null=True)

    # rota
    method = models.CharField(max_length=8, blank=True, null=True)
    path = models.CharField(max_length=512, blank=True, null=True)
    status_code = models.IntegerField(null=True, blank=True)

    # alvo
    app_label = models.CharField(max_length=64, blank=True, null=True)
    model = models.CharField(max_length=64, blank=True, null=True)
    object_id = models.CharField(max_length=64, blank=True, null=True)
    object_repr = models.CharField(max_length=200, blank=True, null=True)
    object_version = models.IntegerField(null=True, blank=True)  # opcional (incremental)

    # ação
    action = models.CharField(max_length=16, choices=Action.choices, default=Action.OTHER)
    reason = models.CharField(max_length=255, blank=True, null=True)        # justificativa (ex.: RGPD)
    company_nif = models.CharField(max_length=16, blank=True, null=True)    # tenant lógico

    # dados
    fields_whitelist = models.JSONField(default=list, blank=True)
    before = models.JSONField(blank=True, null=True)
    after = models.JSONField(blank=True, null=True)
    payload_hash = models.CharField(max_length=64, blank=True, null=True)   # sha256 do body
    file_hash = models.CharField(max_length=64, blank=True, null=True)      # sha256 do ficheiro (se aplicável)
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["occurred_at"]),
            models.Index(fields=["user_id"]),
            models.Index(fields=["company_nif"]),
            models.Index(fields=["app_label", "model", "object_id"]),
            models.Index(fields=["action"]),
        ]
        ordering = ["-occurred_at"]

    def __str__(self):
        return f"{self.occurred_at} {self.action} {self.app_label}.{self.model}:{self.object_id}"
