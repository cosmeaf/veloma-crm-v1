from rest_framework.permissions import BasePermission
from authentication.utils.roles import infer_role, ROLE_CLIENT

class IsStaffOrAdmin(BasePermission):
    def has_permission(self, request, view):
        role = infer_role(request.user)
        return role != ROLE_CLIENT
