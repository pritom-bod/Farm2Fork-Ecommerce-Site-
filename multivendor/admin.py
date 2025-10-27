from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Seller

@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ['shop_name', 'user', 'joined_at']
    list_filter = ['joined_at']
    search_fields = ['shop_name', 'user__username', 'user__email']
    readonly_fields = ['joined_at']

    fieldsets = (
        (None, {
            'fields': ('user', 'shop_name', 'shop_logo', 'bio', 'joined_at'),
        }),
    )
