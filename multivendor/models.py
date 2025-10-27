from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

ORDER_STATUS = (
    ('PENDING', 'Pending'),
    ('PROCESSING', 'Processing'),
    ('ON_THE_WAY', 'On the Way'),
    ('DELIVERED', 'Delivered'),
    ('CANCELLED', 'Cancelled'),
)

class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_account')
    shop_name = models.CharField(max_length=256, unique=True)
    bio = models.TextField(blank=True)
    shop_logo = models.ImageField(upload_to='shop_logo/', blank=True, null=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.shop_name

    def total_sales(self):
        from shop.models import Order
        return sum(order.total for order in self.orders.filter(status='DELIVERED'))

    def order_count(self):
        from shop.models import Order
        return self.orders.count()
