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
        fields = ['id', 'title', 'price', 'featured', 'category', 'category_title']
        extra_kwargs = {
            'category': {'write_only': True}
        }

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
    menuitem_title = serializers.ReadOnlyField(source='menuitem.title')
    class Meta:
        model = Cart
        fields = ['menuitem', 'menuitem_title', 'quantity', 'unit_price', 'price', 'user']
        extra_kwargs = {
            'unit_price': {'read_only': True},
            'price': {'read_only': True}
        }

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
    orderitems = serializers.StringRelatedField(many=True, read_only=True)
    class Meta:
        model = Order
        fields = ['id', 'user_username', 'delivery_crew', 'status', 'total', 'date', 'orderitems']
        extra_kwargs = {
            'date': {'read_only': True},
            'total': {'read_only': True}
        }

    def create(self, validated_data):
        user_id = self.context['request'].user.id
        user = get_object_or_404(User, pk=user_id)
        validated_data['user'] = user
        return super().create(validated_data)
    
class OrderItemSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    menuitem_title = serializers.ReadOnlyField(source='menuitem.title')

    class Meta:
        model = OrderItem
        fields = ['order', 'menuitem_title', 'quantity', 'unit_price', 'price']
        extra_kwargs = {
            'quantity': {'read_only': True},
            'unit_price': {'read_only': True},
            'price': {'read_only': True}
        }