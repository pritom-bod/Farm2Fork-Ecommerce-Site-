# shop/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Avg


# Category Choices
CATEGORY_CHOICES = (
    ('F', 'Fruits'),
    ('V', 'Vegetable'),
    ('DF', 'Dryfruits'),
    ('M', 'Meat'),
    ('FH', 'Fish'),
    ('B', 'Bread'),
)


# Shipping Method Choices
SHIPPING_CHOICES = (
    ('FREE', 'Free Shipping'),
    ('FLAT', 'Flat Rate - $15.00'),
    ('LOCAL', 'Local Pickup - $8.00'),
)


# Payment Method Choices
PAYMENT_CHOICES = (
    ('BANK', 'Direct Bank Transfer'),
    ('CHECK', 'Check Payments'),
    ('COD', 'Cash On Delivery'),
    ('PAYPAL', 'Paypal'),
)


# Order Status Choices
ORDER_STATUS = (
    ('PENDING', 'Pending'),
    ('PROCESSING', 'Processing'),
    ('SHIPPED', 'Shipped'),
    ('DELIVERED', 'Delivered'),
    ('CANCELLED', 'Cancelled'),
)



class Tag(models.Model):
    """Tags for products (e.g., organic, fresh, etc.)"""
    name = models.CharField(max_length=50, unique=True)


    def __str__(self):
        return self.name



class Product(models.Model):
    seller = models.ForeignKey('multivendor.Seller', on_delete=models.CASCADE, null=True, blank=True, related_name='products')
    title = models.CharField(max_length=100)
    regular_price = models.FloatField()
    discounted_price = models.FloatField()
    descriptions = models.TextField()
    category = models.CharField(max_length=2)  # your categories
    product_image = models.ImageField(upload_to='product_image/')
    tags = models.ManyToManyField('Tag', blank=True)


    def __str__(self):
        return self.title


    class Meta:
        ordering = ['-id']
    
    def average_rating(self):
        """Calculate average rating"""
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0
    
    def total_reviews(self):
        """Total number of reviews"""
        return self.reviews.count()
    
    def get_category_display_full(self):
        """Get full category name"""
        return dict(CATEGORY_CHOICES).get(self.category, '')



class Cart(models.Model):
    """Shopping cart for each user"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


    def total(self):
        """Calculate total cart value"""
        return sum(item.subtotal() for item in self.items.all())


    def __str__(self):
        return f"Cart for {self.user.username}"



class CartItem(models.Model):
    """Individual items in a shopping cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


    def subtotal(self):
        """Calculate subtotal for this cart item"""
        return self.quantity * self.product.discounted_price


    def __str__(self):
        return f"{self.quantity} x {self.product.title}"



class UserProfile(models.Model):
    """Extended user profile with additional information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', null=True, blank=True)
    first_name = models.CharField(max_length=50, blank=True, default='')
    last_name = models.CharField(max_length=50, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    address = models.CharField(max_length=1000, blank=True, default='')
    city = models.CharField(max_length=50, blank=True, default='')
    country = models.CharField(max_length=50, default='Bangladesh')
    postcode = models.CharField(max_length=20, blank=True, default='')
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.username if self.user else 'No User'}'s Profile"


    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'



class Order(models.Model):
    """Customer orders"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    
    # Billing Information
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    company_name = models.CharField(max_length=100, blank=True, default='')
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=1000)
    city = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    postcode = models.CharField(max_length=20)
    
    # Shipping Information
    shipping_method = models.CharField(max_length=10, choices=SHIPPING_CHOICES, default='FREE')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Payment Information
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    
    # Order Details
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='PENDING')
    notes = models.TextField(blank=True, default='')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    def get_shipping_cost(self):
        """Get shipping cost based on shipping method"""
        shipping_costs = {
            'FREE': 0.00,
            'FLAT': 15.00,
            'LOCAL': 8.00,
        }
        return shipping_costs.get(self.shipping_method, 0.00)



class OrderItem(models.Model):
    """Individual items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.title}"


    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'



class ProductReview(models.Model):
    """Product reviews by verified buyers only"""
    RATING_CHOICES = (
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)  # Verify purchase
    rating = models.IntegerField(choices=RATING_CHOICES)
    review = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('product', 'user', 'order')  # One review per product per order
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.title} ({self.rating} stars)"
    

class ProductQuestion(models.Model):
    """Public Q&A for products - visible to everyone"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='questions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_questions')
    question = models.TextField()
    answer = models.TextField(blank=True, null=True)
    answered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='answered_questions')
    is_answered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Q: {self.question[:50]} - {self.product.title}"

class ProductQuestion(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='questions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_questions')
    question = models.TextField()
    answer = models.TextField(blank=True, null=True)
    answered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='answered_questions')
    is_answered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(blank=True, null=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f"Q: {self.question[:50]} - {self.product.title}"