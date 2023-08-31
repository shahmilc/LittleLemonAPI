from django.shortcuts import render, get_object_or_404
from rest_framework import generics, viewsets, response, status
from rest_framework.permissions import BasePermission, IsAuthenticated, IsAdminUser
from .models import MenuItem, Cart, OrderItem, Order
from .serializers import MenuItemSerializer, UserSerializer, CartSerializer, OrderItemSerializer
from django.contrib.auth.models import User, Group
from rest_framework.decorators import api_view, permission_classes
import datetime

class IsManagerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'GET':
            return True
        return request.user.is_authenticated and request.user.groups.filter(name='Manager').exists()
    
class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name='Manager').exists()
    
class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsManagerOrReadOnly]


class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsManagerOrReadOnly]


class ManagerView(viewsets.ViewSet):
    permission_classes = [IsManager]
    def list(self, request):
        group = Group.objects.get(name='Manager')
        serializer = UserSerializer(group.user_set.all(), many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
            group = Group.objects.get(name='Manager')
            group.user_set.add(user)
            
        return response.Response({'message': 'user added'}, status=status.HTTP_201_CREATED)
        
    def destroy(self, request, pk=None):
        if pk:
            user = get_object_or_404(User, pk=pk)
            group = Group.objects.get(name='Manager')
            group.user_set.remove(user)
            return response.Response({'message': 'user removed'}, status=status.HTTP_200_OK)
        return response.Response({'message': 'user not found'}, status=status.HTTP_404_NOT_FOUND)
    
class DeliveryCrewView(viewsets.ViewSet):
    permission_classes = [IsManager]
    def list(self, request):
        group = Group.objects.get(name='Delivery Crew')
        serializer = UserSerializer(group.user_set.all(), many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
            group = Group.objects.get(name='Delivery Crew')
            group.user_set.add(user)
            
        return response.Response({'message': 'user added'}, status=status.HTTP_201_CREATED)
        
    def destroy(self, request, pk=None):
        if pk:
            user = get_object_or_404(User, pk=pk)
            group = Group.objects.get(name='Delivery Crew')
            group.user_set.remove(user)
            return response.Response({"message": "user removed"}, status=status.HTTP_200_OK)
        return response.Response({'message': 'user not found'}, status=status.HTTP_404_NOT_FOUND)
    
class CartView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request':self.request})
        return context
    
    def delete(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset.delete()
        return response.Response({'message': 'cart deleted'}, status=status.HTTP_200_OK)
    
class OrderView(generics.ListCreateAPIView):
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_orders = Order.objects.filter(user=self.request.user)
        return OrderItem.objects.filter(order__in=user_orders)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context
    
    def create(self, request, *args, **kwargs):
        cart = Cart.objects.filter(user=self.request.user)
        if cart.count() > 0:
            
            order = Order(
                user = request.user,
                total = 0.0,
                date = datetime.datetime.now()
            )
            order.save()

            for item in cart:
                order_item = OrderItem(
                    order = order,
                    menuitem = item.menuitem,
                    quantity = item.quantity,
                    unit_price = item.unit_price,
                    price = item.price
                )
                order.total += float(item.price)
                order_item.save()
                order.save()
            cart.delete()
            return response.Response({'message': 'order created'}, status=status.HTTP_200_OK)
        
        return response.Response({'message': 'failed to create order - empty cart'}, status=status.HTTP_400_BAD_REQUEST)
    

