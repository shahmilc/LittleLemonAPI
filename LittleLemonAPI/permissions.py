from rest_framework.permissions import BasePermission

class IsManagerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'GET':
            return True
        return request.user.is_authenticated and request.user.groups.filter(name='Manager').exists()
    
class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name='Manager').exists()
    
class IsDeliveryCrew(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name='Delivery crew').exists()