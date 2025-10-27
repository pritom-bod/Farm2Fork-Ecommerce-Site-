from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Seller
from shop.models import Product

class SellerRegisterForm(UserCreationForm):
    shop_name = forms.CharField(max_length=256, required=True)
    bio = forms.CharField(widget=forms.Textarea, required=False)
    shop_logo = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')  # fixed: NO seller fields here

class SellerLoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)

class SellerProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'regular_price', 'discounted_price', 'descriptions', 'category', 'product_image', 'tags']




class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = Seller
        fields = ['shop_name', 'bio', 'shop_logo']
        widgets = {
            'shop_name': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'shop_logo': forms.FileInput(attrs={'class': 'form-control'}),
        }