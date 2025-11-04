from django.contrib import admin
from .models import AuditEvent

@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("occurred_at","action","user","path","app_label","model","object_id","status_code")
    list_filter = ("action","app_label","model","status_code","user_is_staff","user_is_superuser")
    search_fields = ("path","user_repr","object_id","request_id","company_nif")
    readonly_fields = [f.name for f in AuditEvent._meta.fields]
