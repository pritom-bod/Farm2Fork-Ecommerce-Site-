from django.db import models
from django.contrib.auth.models import User
# Create your models here.
CATEGORY_CHOICES = (
    ('F','Fruits'),
    ('V','Vegetable'),
    ('DF','Dryfruits'),
    ('M','meat'),
    ('FH','Fish'),
    ('B','Bread'),

)

class Product(models.Model):
    title = models.CharField(max_length=100)
    regular_price = models.FloatField()
    discounted_price = models.FloatField()
    descriptions = models.TextField()
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)
    product_image = models.ImageField(upload_to='product_image')

    def __str__(self):
        return str(self.id)


#profile create model

class UserProfile(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    number = models.IntegerField(unique=True)
    address = models.CharField(max_length=1000)
    city =models.CharField(max_length=50)
    country= models.CharField(max_length=50, default='Bangladesh')
    postcode = models.IntegerField()
