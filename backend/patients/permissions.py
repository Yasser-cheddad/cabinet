from rest_framework import permissions

class IsDoctorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow doctors to edit patients.
    Read-only permissions are allowed for any authenticated user.
    """
    
    def has_permission(self, request, view):
        # Allow read-only permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write permissions are only allowed to doctors
        return request.user and request.user.is_authenticated and hasattr(request.user, 'doctor_profile')
        
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
            
        # Write permissions are only allowed to doctors
        return request.user and request.user.is_authenticated and hasattr(request.user, 'doctor_profile')
