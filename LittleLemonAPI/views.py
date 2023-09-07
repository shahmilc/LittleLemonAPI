from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User, Group
from rest_framework import generics, viewsets, response, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied
from .permissions import IsManager, IsManagerOrReadOnly, IsDeliveryCrew
from .models import Category, MenuItem, Cart, OrderItem, Order
from .serializers import CategorySerializer, MenuItemSerializer, UserSerializer, CartSerializer, OrderItemSerializer, OrderSerializer

import datetime
    
class CategoryView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsManager]

class SingleCategoryView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsManager]

class MenuItemsView(generics.ListCreateAPIView):
    # select_related reduces database hits at the serializer
    queryset = MenuItem.objects.all().select_related('category')
    serializer_class = MenuItemSerializer
    permission_classes = [IsManagerOrReadOnly]
    ordering_fields = ['price', 'category']
    search_fields = ['title', 'category']

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

    # Users can only see their own Cart
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
    permission_classes = [IsAuthenticated]
    ordering_fields = ['user_username', 'delivery_crew', 'status', 'date', 'total']

    def get_queryset(self):
        # Managers can see all Orders
        if IsManager.has_permission(self, self.request, None):
            return Order.objects.all().prefetch_related('orderitems').all()
        # Delivery crew can only see Orders they're assigned to deliver
        if IsDeliveryCrew.has_permission(self, self.request, None):
            return Order.objects.filter(delivery_crew=self.request.user).prefetch_related('orderitems').all()
        # Customers can see their own orders
        return Order.objects.filter(user=self.request.user).prefetch_related('orderitems').all()

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return OrderSerializer
        else:
            return OrderItemSerializer

    # POST request sent to endpoint should retrieve all items in Cart, create an Order,
    # create OrderItems for all the Cart items, assign the OrderItems to the Order
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
    queryset = Order.objects.all().prefetch_related('orderitems')

    def check_permissions(self, request):
        is_manager = IsManager.has_permission(self, self.request, None)
        is_delivery_crew = IsDeliveryCrew.has_permission(self, self.request, None)
        # Allow only Managers and the Order's customer to see a specific Order
        if request.method in SAFE_METHODS:
            pk = self.kwargs['pk']
            order = get_object_or_404(Order, pk=pk)
            if not is_manager and order.user != request.user:
                raise PermissionDenied()
        # Allow only Managers and Delivery crew to make partial updates
        if request.method == 'PATCH':
            if not (is_manager or is_delivery_crew):
                raise PermissionDenied()
        # Allow only Managers to completely change or delete Orders
        if request.method == 'PUT' or request.method == 'DELETE':
            if not is_manager:
                raise PermissionDenied()

        return super().check_permissions(request)

    def patch(self, request, *args, **kwargs):
        # Delivery crew can only change Order status
        if not IsManager.has_permission(self, request, None):
            instance = self.get_object()
            instance.status = request.data['status']
            instance.save()
            serializer = self.get_serializer(instance)
            return response.Response(serializer.data, status=status.HTTP_200_OK)
        return super().patch(request, *args, **kwargs)
    