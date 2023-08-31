from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from .models import Category, MenuItem, Cart, Order, OrderItem

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title']

class MenuItemSerializer(serializers.ModelSerializer):
    category_title = serializers.ReadOnlyField(source='category.title')
    class Meta:
        model = MenuItem
        fields = ['title', 'price', 'featured', 'category_title']

class UserSerializer(serializers.ModelSerializer):
    email = serializers.CharField(read_only=True)
    id = serializers.IntegerField(read_only=True)
    
    def validate_username(self, value):
        try:
            User.objects.get(username=value)
        except ObjectDoesNotExist:
            raise serializers.ValidationError("User with this username does not exist.")
        return value
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class CartSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    unit_price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    class Meta:
        model = Cart
        fields = ['menuitem', 'quantity', 'unit_price', 'price', 'user']

    def create(self, validated_data):
        user_id = self.context['request'].user.id
        user = get_object_or_404(User, pk=user_id)
        unit_price = validated_data['menuitem'].price
        price = unit_price * validated_data['quantity']
        validated_data['user'] = user
        validated_data['unit_price'] = unit_price
        validated_data['price'] = price
        return super().create(validated_data)

class OrderSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')
    total = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    date = serializers.DateField(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user_username', 'delivery_crew', 'status', 'total', 'date']

    def create(self, validated_data):
        user_id = self.context['request'].user.id
        user = get_object_or_404(User, pk=user_id)
        validated_data['user'] = user
        return super().create(validated_data)
    
class OrderItemSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    menuitem_title = serializers.ReadOnlyField(source='menuitem.title')
    quantity = serializers.IntegerField(read_only=True)
    unit_price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['order', 'menuitem_title', 'quantity', 'unit_price', 'price']