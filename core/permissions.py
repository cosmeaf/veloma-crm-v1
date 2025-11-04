from rest_framework import permissions


class IsSuperUser(permissions.BasePermission):
    """Permite tudo apenas ao superusuário."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class IsStaff(permissions.BasePermission):
    """Permite acesso total ao staff (mas não ao superuser)."""
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.is_staff and not request.user.is_superuser
        )


class IsRegularUser(permissions.BasePermission):
    """Usuário comum (nem staff, nem superuser)."""
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and not request.user.is_staff and not request.user.is_superuser
        )


class IsOwnerOrStaffOrSuperUser(permissions.BasePermission):
    """
    - Superuser → acesso total
    - Staff → acesso total
    - User → apenas se for o dono (obj.user == request.user)
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        return getattr(obj, "user_id", None) == request.user.id

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
