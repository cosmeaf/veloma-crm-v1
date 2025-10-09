from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

ROLE_ADMIN = "admin"    # superuser (gestão do projeto Django)
ROLE_STAFF = "staff"    # gestor da aplicação
ROLE_CLIENT = "client"  # cliente

User = get_user_model()

def ensure_default_groups() -> None:
    Group.objects.get_or_create(name=ROLE_STAFF)
    Group.objects.get_or_create(name=ROLE_CLIENT)

def infer_role(user: User) -> str:
    if user.is_superuser:
        return ROLE_ADMIN
    if user.is_staff:
        return ROLE_STAFF
    return ROLE_CLIENT
