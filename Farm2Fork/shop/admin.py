from django.contrib import admin
from .models import Product, UserProfile
# Register your models here.

@admin.register(Product)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ['title', 'regular_price', 'discounted_price', 'descriptions', 'category', 'product_image']


@admin.register(UserProfile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'email', 'address', 'postcode', 'number']