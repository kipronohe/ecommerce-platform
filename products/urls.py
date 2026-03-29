from django.urls import path,  include
from . import views

urlpatterns = [
    
    path('', views.product_list, name='home'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),

        # NEW
    path('increase/<int:product_id>/', views.increase_quantity, name='increase_quantity'),
    path('decrease/<int:product_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', views.register, name='register'),
    path('orders/', views.order_history, name='order_history'),
    path('pay/<int:order_id>/', views.pay_order, name='pay_order'),
    path('search/', views.search_products, name='search_products'),
    # products/urls.py
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('', views.home, name='home'),
    
]