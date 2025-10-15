# models.py (Unchanged from previous, but included for completeness)
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
CATEGORY_CHOICES = (
    ('F', 'Fruits'),
    ('V', 'Vegetable'),
    ('DF', 'Dryfruits'),
    ('M', 'meat'),
    ('FH', 'Fish'),
    ('B', 'Bread'),
)

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    title = models.CharField(max_length=100)
    regular_price = models.FloatField()
    discounted_price = models.FloatField()
    descriptions = models.TextField()
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)
    product_image = models.ImageField(upload_to='product_image')
    tags = models.ManyToManyField(Tag, blank=True)  # For filters like organic, fresh, etc.

    def __str__(self):
        return str(self.id)

# Cart Model
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def total(self):
        return sum(item.subtotal() for item in self.items.all())

    def __str__(self):
        return f"Cart for {self.user.username}"

# CartItem Model
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.quantity * self.product.discounted_price

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"

# Profile create model
class UserProfile(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    number = models.IntegerField(unique=True)
    address = models.CharField(max_length=1000)
    city = models.CharField(max_length=50)
    country = models.CharField(max_length=50, default='Bangladesh')
    postcode = models.IntegerField()