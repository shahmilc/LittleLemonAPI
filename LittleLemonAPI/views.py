from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User, Group
from rest_framework import generics, viewsets, response, status
from rest_framework.permissions import BasePermission, IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from .models import Category, MenuItem, Cart, OrderItem, Order
from .serializers import CategorySerializer, MenuItemSerializer, UserSerializer, CartSerializer, OrderItemSerializer, OrderSerializer

import datetime

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
    
class CategoryView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]

class SingleCategoryView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]

class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAdminUser|IsManagerOrReadOnly]
    ordering_fields = ['price', 'category']

class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsManagerOrReadOnly]


class ManagerView(viewsets.ViewSet):
    permission_classes = [IsAdminUser]
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
            
        return response.Response({'detail': 'user added'}, status=status.HTTP_201_CREATED)
        
    def destroy(self, request, pk=None):
        if pk:
            user = get_object_or_404(User, pk=pk)
            group = Group.objects.get(name='Manager')
            group.user_set.remove(user)
            return response.Response({'detail': 'user removed'}, status=status.HTTP_200_OK)
        return response.Response({'detail': 'user not found'}, status=status.HTTP_404_NOT_FOUND)
    
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
            
        return response.Response({'detail': 'user added'}, status=status.HTTP_201_CREATED)
        
    def destroy(self, request, pk=None):
        if pk:
            user = get_object_or_404(User, pk=pk)
            group = Group.objects.get(name='Delivery Crew')
            group.user_set.remove(user)
            return response.Response({"detail": "user removed"}, status=status.HTTP_200_OK)
        return response.Response({'detail': 'user not found'}, status=status.HTTP_404_NOT_FOUND)
    
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
        return response.Response({'detail': 'cart deleted'}, status=status.HTTP_200_OK)
    
class OrderView(generics.ListCreateAPIView):
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if IsManager.has_permission(self, self.request, None):
            return OrderItem.objects.all()
        if IsDeliveryCrew.has_permission(self, self.request, None):
            delivery_orders = Order.objects.filter(delivery_crew=self.request.user)
            return OrderItem.objects.filter(order__in=delivery_orders)
        user_orders = Order.objects.filter(user=self.request.user)
        return OrderItem.objects.filter(order__in=user_orders)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context
    
    def post(self, request, *args, **kwargs):
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
            return response.Response({'detail': 'order created'}, status=status.HTTP_200_OK)
        
        return response.Response({'detail': 'failed to create order - empty cart'}, status=status.HTTP_400_BAD_REQUEST)
    

class SingleOrderView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def check_permissions(self, request):
        if request.method == 'PATCH':
            if not (IsManager.has_permission(self, self.request, None) or IsDeliveryCrew.has_permission(self, self.request, None)):
                raise PermissionDenied()
        if request.method == 'PUT' or request.method == 'DELETE':
            if not IsManager.has_permission(self, self.request, None):
                raise PermissionDenied()

    def get_queryset(self):
        pk = self.kwargs['pk']

        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return Order.objects.filter(pk=pk)

        if not IsAuthenticated.has_permission(self, self.request, None):
            raise PermissionDenied('you must be logged in to view your order')
        
        order = get_object_or_404(Order, pk=pk)
        if IsManager.has_permission(self, self.request, None) or order.user == self.request.user or order.delivery_crew == self.request.user:
            return OrderItem.objects.filter(order=order)
        else:
            return response.Response({'detail': 'order does not belong to user'}, status=status.HTTP_401_UNAUTHORIZED)
    
    def get(self, request, *args, **kwargs):
        order = self.get_queryset()
        serializer = OrderItemSerializer(instance=order, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, *args, **kwargs):
        # Delivery crew can only change Order status
        if not IsManager.has_permission(self, request, None):
            instance = self.get_object()
            instance.status = request.data['status']
            instance.save()
            serializer = self.get_serializer(instance)
            return response.Response(serializer.data, status=status.HTTP_200_OK)
        return super().patch(request, *args, **kwargs)
    