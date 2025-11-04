from django.db.models.signals import post_save, post_delete
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.utils.module_loading import import_string
from .models import AuditEvent
from .utils import model_to_dict, get_groups_snapshot

# --- Config de whitelist por modelo (ajuste conforme necessidade) ---
WHITELIST = {
    # "app_label.ModelName": ["field1","field2",...]
    "authentication.OtpCode": ["id","user_id","created_at","is_used"],
    "authentication.ResetPasswordToken": ["id","user_id","created_at"],
    # adicione aqui modelos sensíveis com campos permitidos
}

def _fields_for(obj):
    key = f"{obj._meta.app_label}.{obj.__class__.__name__}"
    return WHITELIST.get(key, [])

def _common_event_kwargs(user):
    if user and getattr(user, "is_authenticated", False):
        return dict(
            user=user,
            user_repr=getattr(user, "email", None),
            user_is_staff=user.is_staff,
            user_is_superuser=user.is_superuser,
            user_groups=get_groups_snapshot(user),
        )
    return dict(user=None, user_repr=None, user_is_staff=False, user_is_superuser=False, user_groups=[])

@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    AuditEvent.objects.create(
        **_common_event_kwargs(user),
        method=getattr(request, "method", None),
        path=getattr(request, "path", None),
        ip=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        request_id=getattr(request, "request_id", None),
        action=AuditEvent.Action.LOGIN,
    )

@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs):
    AuditEvent.objects.create(
        **_common_event_kwargs(user),
        method=getattr(request, "method", None) if request else None,
        path=getattr(request, "path", None) if request else None,
        ip=request.META.get("REMOTE_ADDR") if request else None,
        user_agent=request.META.get("HTTP_USER_AGENT", "") if request else None,
        request_id=getattr(request, "request_id", None) if request else None,
        action=AuditEvent.Action.LOGOUT,
    )

def connect_signals():
    post_save.connect(model_saved_handler, dispatch_uid="auditlog_model_saved")
    post_delete.connect(model_deleted_handler, dispatch_uid="auditlog_model_deleted")

def _actor_from_instance(instance):
    # tenta achar um atributo padrão com o autor (se você setar em views)
    return getattr(instance, "_audit_actor", None)

def _company_from_instance(instance):
    return getattr(instance, "company_nif", None) or getattr(getattr(instance, "company", None), "nif", None)

def _object_meta(instance):
    ct = ContentType.objects.get_for_model(instance.__class__)
    return ct.app_label, ct.model

def model_saved_handler(sender, instance, created, **kwargs):
    try:
        actor = _actor_from_instance(instance)
        fields = _fields_for(instance)
        app_label, model = _object_meta(instance)
        action = AuditEvent.Action.CREATE if created else AuditEvent.Action.UPDATE
        data = model_to_dict(instance, fields=fields) if fields else None
        AuditEvent.objects.create(
            **_common_event_kwargs(actor),
            app_label=app_label, model=model,
            object_id=str(getattr(instance, "pk", None)),
            object_repr=str(instance),
            action=action,
            fields_whitelist=fields,
            after=data,
            company_nif=_company_from_instance(instance),
        )
    except Exception:
        pass

def model_deleted_handler(sender, instance, **kwargs):
    try:
        actor = _actor_from_instance(instance)
        fields = _fields_for(instance)
        app_label, model = _object_meta(instance)
        data = model_to_dict(instance, fields=fields) if fields else None
        AuditEvent.objects.create(
            **_common_event_kwargs(actor),
            app_label=app_label, model=model,
            object_id=str(getattr(instance, "pk", None)),
            object_repr=str(instance),
            action=AuditEvent.Action.DELETE,
            fields_whitelist=fields,
            before=data,
            company_nif=_company_from_instance(instance),
        )
    except Exception:
        pass
