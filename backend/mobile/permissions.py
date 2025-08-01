from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners of an object to edit it."""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.seller == request.user

class IsBuyerOrSeller(permissions.BasePermission):
    """Custom permission to only allow buyer or seller of an order."""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for buyer or seller
        if request.method in permissions.SAFE_METHODS:
            return obj.buyer == request.user or obj.seller == request.user
        
        # Write permissions are only allowed to the seller
        return obj.seller == request.user

class IsAdminUser(permissions.BasePermission):
    """Custom permission to only allow admin users."""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'ADMIN'

class IsOwner(permissions.BasePermission):
    """Custom permission to only allow the owner of an object."""
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """Custom permission to allow read access to anyone, but require authentication for write."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated 