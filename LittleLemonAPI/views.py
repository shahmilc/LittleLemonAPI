from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User, Group
from rest_framework import generics, viewsets, response, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from .permissions import IsManager, IsManagerOrReadOnly, IsDeliveryCrew
from .models import Category, MenuItem, Cart, OrderItem, Order
from .serializers import CategorySerializer, MenuItemSerializer, UserSerializer, CartSerializer, OrderItemSerializer, OrderSerializer

import datetime
    
class CategoryView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]

class SingleCategoryView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]

class MenuItemsView(generics.ListCreateAPIView):
    # select_related reduces database hits at the serializer
    queryset = MenuItem.objects.all().select_related('category')
    serializer_class = MenuItemSerializer
    permission_classes = [IsAdminUser|IsManagerOrReadOnly]
    ordering_fields = ['price', 'category']

class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsManagerOrReadOnly]

class BaseGroupView(viewsets.ViewSet):
    permission_classes = None
    group_name = None

    def list(self, request):
        group = Group.objects.get(name=self.group_name)
        serializer = UserSerializer(group.user_set.all(), many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
            group = Group.objects.get(name=self.group_name)
            group.user_set.add(user)
            
        return response.Response({'detail': 'user added'}, status=status.HTTP_201_CREATED)
        
    def destroy(self, request, pk=None):
        if pk:
            user = get_object_or_404(User, pk=pk)
            group = Group.objects.get(name=self.group_name)
            group.user_set.remove(user)
            return response.Response({'detail': 'user removed'}, status=status.HTTP_200_OK)
        return response.Response({'detail': 'user not found'}, status=status.HTTP_404_NOT_FOUND)

class ManagerView(BaseGroupView):
    # Allow only Admin superusers to add or remove Managers
    permission_classes = [IsAdminUser]
    group_name = 'Manager'

class DeliveryCrewView(BaseGroupView):
    # Allow only Managers to add, remove, or assign Delivery crews
    permission_classes = [IsManager]
    group_name = 'Delivery crew'
    
class CartView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).select_related('user').select_related('menuitem')
    
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
            return OrderItem.objects.all().select_related('order')
        if IsDeliveryCrew.has_permission(self, self.request, None):
            delivery_orders = Order.objects.filter(delivery_crew=self.request.user)
            return OrderItem.objects.filter(order__in=delivery_orders).select_related('order')
        user_orders = Order.objects.filter(user=self.request.user)
        return OrderItem.objects.filter(order__in=user_orders).select_related('order')
    
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
        # Allow only Managers and Delivery crew to make partial updates
        if request.method == 'PATCH':
            if not (IsManager.has_permission(self, self.request, None) or IsDeliveryCrew.has_permission(self, self.request, None)):
                raise PermissionDenied()
        # Allow only Managers to completely change or delete orders
        if request.method == 'PUT' or request.method == 'DELETE':
            if not IsManager.has_permission(self, self.request, None):
                raise PermissionDenied()

    def get_queryset(self):
        pk = self.kwargs['pk']

        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return Order.objects.filter(pk=pk)
        
        order = get_object_or_404(Order, pk=pk)
        # User can view an order if they're a Manager, or if its their own order, or for Delivery crews if it's their order to deliver
        if IsManager.has_permission(self, self.request, None) or order.user == self.request.user or order.delivery_crew == self.request.user:
            return OrderItem.objects.filter(order=order).select_related('order')
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
    