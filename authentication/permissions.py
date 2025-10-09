from rest_framework.permissions import BasePermission, SAFE_METHODS
from .utils.roles import infer_role, ROLE_ADMIN, ROLE_STAFF, ROLE_CLIENT

class IsProjectAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)

class IsAppStaff(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return infer_role(request.user) in (ROLE_ADMIN, ROLE_STAFF)

class IsClient(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return infer_role(request.user) == ROLE_CLIENT

class StaffOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return infer_role(request.user) in (ROLE_ADMIN, ROLE_STAFF)
