from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.user == request.user


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Custom permission to only allow owners or staff to view or edit an object.
    """
    
    def has_object_permission(self, request, view, obj):
        # Staff permissions
        if request.user.is_staff or request.user.user_type in ['admin', 'provider', 'dispatcher']:
            return True

        # Owner permissions
        try:
            return obj.user == request.user
        except AttributeError:
            return False


class IsProviderOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow providers or admins to view or edit an object.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_staff or request.user.user_type in ['admin', 'provider']