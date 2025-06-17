from django.shortcuts import render
from .models import Product, UserProfile
from django.views import View
from django.contrib import messages
from .forms import UserRegForm, LoginForm, PassChangeForm
# Create your views here.

class ProductView(View):
    def get(self, request):
        allproducts = Product.objects.all()
        fruits = Product.objects.filter(category='F')
        vegetables = Product.objects.filter(category='V')
        meat = Product.objects.filter(category='M')
        bread = Product.objects.filter(category='B')
        return render(request, 'shop/index.html', {
            'allproducts':allproducts,
            'fruits':fruits,
            'vegetables':vegetables,
            'meat':meat,
            'bread':bread,

        })

def shop(request, data=None):
    if data == None:
        products = Product.objects.all()
    elif data == 'Fish':
        products = Product.objects.filter(category='FH')
    elif data == 'Dryfruits':
        products = Product.objects.filter(category='DF')
    elif data == 'Fruits':
        products = Product.objects.filter(category='F')
    elif data == 'Vegetable':
        products = Product.objects.filter(category='V')
    elif data == 'meat':
        products = Product.objects.filter(category='M')

    price = request.GET.get('price')  
    if price:
        try:
            price = int(price)
            products = products.filter(discounted_price__lte=price)  # Filter products# by tk
        except ValueError:
            pass  

    return render(request, 'shop/shop.html', {
        'products': products
    })



def cart(request):
    return render(request, 'shop/cart.html')


def chackout(request):
        return render(request, 'shop/chackout.html')

class ProductDetails(View):
    def get(self, request, pk):
        product = Product.objects.get(pk=pk)
        return render(request, 'shop/product-detail.html', {
            'product':product
        })
def contact(request):
    return render(request, 'shop/contact.html')
def testimonial(request):
    return render(request, 'shop/testimonial.html')
def E_page(request):
    return render(request, 'shop/404.html')
def Profile(request):
    if request.method == 'POST':
        first_name =  request.POST.get('firstname')
        last_name =  request.POST.get('lastname')
        email = request.POST.get('email')
        address = request.POST.get('address')
        city = request.POST.get('city')
        country = request.POST.get('country')
        postcode = request.POST.get('postcode')
        mobile = request.POST.get('mobile')

        Profile = UserProfile(first_name=first_name, last_name=last_name, email=email, address=address, city=city, country=country, postcode=postcode, number=mobile)
        Profile.save()
        return render(request, 'shop/profile.html', {'userprofile':Profile})
   
    return render(request, 'shop/profile.html')

class userregistration(View):
    def get(self, request):
        form = UserRegForm()
        return render(request, 'shop/registration.html',{'form':form})
    
    def post(self,request):
        form =UserRegForm(request.POST)
        if form.is_valid():
            messages.success(request, 'Congratulattion, User Created')
            form.save()
        return render(request, 'shop/registration.html', {'form':form})
