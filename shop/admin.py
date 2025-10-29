from django.contrib import admin
from .models import Product, Tag, Cart, CartItem, UserProfile, Order, OrderItem, ProductQuestion

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'category', 'regular_price', 'discounted_price']
    list_filter = ['category', 'tags']
    search_fields = ['title', 'descriptions']

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'first_name', 'last_name', 'email', 'phone', 'city']
    search_fields = ['user__username', 'email', 'phone']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price', 'subtotal']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'email', 'total', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'shipping_method', 'created_at']
    search_fields = ['order_number', 'user__username', 'email', 'phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'created_at', 'updated_at')
        }),
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'company_name', 'email', 'phone')
        }),
        ('Shipping Address', {
            'fields': ('address', 'city', 'country', 'postcode', 'shipping_method', 'shipping_cost')
        }),
        ('Payment & Totals', {
            'fields': ('payment_method', 'subtotal', 'total')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
    )

admin.site.register(ProductQuestion)
