from django.urls import path
from . import views

urlpatterns = [
    path('menu-items', views.MenuItemsView.as_view(), name='MenuItemsView'),
    path('menu-items/<int:pk>', views.SingleMenuItemView.as_view(), name='SingleMenuItemView'),

    path('groups/manager/users', views.ManagerView.as_view({'get': 'list', 'post': 'create',}), name='ManagerView'),
    path('groups/manager/users/<int:pk>', views.ManagerView.as_view({'delete': 'destroy',})),

    path('groups/delivery-crew/users', views.DeliveryCrewView.as_view({'get': 'list', 'post': 'create',}), name='DeliveryCrewView'),
    path('groups/delivery-crew/users/<int:pk>', views.DeliveryCrewView.as_view({'delete': 'destroy',})),

    path('cart/menu-items', views.CartView.as_view(), name='CartView'),

    path('orders', views.OrderView.as_view(), name='OrderView'),
]