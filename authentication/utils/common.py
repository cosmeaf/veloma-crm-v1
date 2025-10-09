# authentication/utils/common.py
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

User = get_user_model()

def clean_email(email: str) -> str:
    return (email or "").strip().lower()

def ensure_group(user: User, group_name: str) -> None:
    g, _ = Group.objects.get_or_create(name=group_name)
    g.user_set.add(user)

def user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }



