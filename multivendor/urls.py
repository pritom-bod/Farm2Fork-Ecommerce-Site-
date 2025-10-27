from django.urls import path
from . import views

app_name = 'multivendor'

urlpatterns = [
    path('seller/register/', views.seller_register, name='seller_register'),
    path('seller/login/', views.seller_login, name='seller_login'),
    path('seller/logout/', views.seller_logout, name='seller_logout'),
    path('seller/dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('seller/add-product/', views.seller_add_product, name='seller_add_product'),
    path('seller/orders/', views.seller_orders, name='seller_orders'),  # <-- This must match view name
    path('seller/profile/', views.seller_profile, name='seller_profile'),
    path('seller/all-products/', views.seller_all_products, name='seller_all_products'),
]
