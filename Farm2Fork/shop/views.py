# views.py (Updated shop view for advanced nested filters, search, sorting, featured, pagination, categories)
from django.shortcuts import render, get_object_or_404
from .models import Product, UserProfile, Cart, CartItem, Tag
from django.views import View
from django.contrib import messages
from .forms import UserRegForm, LoginForm, PassChangeForm
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Q, Count
from django.core.paginator import Paginator

# Helper function to get or create cart for logged-in user
def get_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    else:
        return None  # For now, assume logged-in; extend for sessions if needed

class ProductView(View):
    def get(self, request):
        allproducts = Product.objects.all()
        fruits = Product.objects.filter(category='F')
        vegetables = Product.objects.filter(category='V')
        meat = Product.objects.filter(category='M')
        bread = Product.objects.filter(category='B')
        return render(request, 'shop/index.html', {
            'allproducts': allproducts,
            'fruits': fruits,
            'vegetables': vegetables,
            'meat': meat,
            'bread': bread,
        })

def shop(request, data=None):
    products = Product.objects.all()

    # Category filter from URL slug (nested with other filters)
    if data:
        category_map = {
            'Dryfruits': 'DF',
            'Fish': 'FH',
            'Fruits': 'F',
            'Vegetable': 'V',
            'meat': 'M',
        }
        cat_code = category_map.get(data)
        if cat_code:
            products = products.filter(category=cat_code)

    # Price filter (nested)
    price = request.GET.get('price')
    if price:
        try:
            products = products.filter(discounted_price__lte=int(price))
        except ValueError:
            pass

    # Status (tags) filter - multiple checkboxes, using AND/OR logic (here OR for multiple)
    status_list = request.GET.getlist('status')
    if status_list:
        q = Q()
        for status in status_list:
            q |= Q(tags__name__iexact=status)  # OR for multiple statuses
        products = products.filter(q).distinct()

    # Search filter (nested, searches title or description)
    search = request.GET.get('search')
    if search:
        products = products.filter(Q(title__icontains=search) | Q(descriptions__icontains=search))

    # Sorting (nested after filters)
    sort = request.GET.get('sort')
    if sort == 'popularity':
        # Assume popularity by some metric, e.g., reverse ID for newer first
        products = products.order_by('-id')
    elif sort == 'organic':
        products = products.filter(tags__name__iexact='organic').distinct().order_by('title')
    elif sort == 'fantastic':
        products = products.order_by('-discounted_price')  # Example: high to low price
    # Add more sorts as needed

    # Featured products - e.g., annotated with tag count or random
    featured_products = Product.objects.annotate(tag_count=Count('tags')).filter(tag_count__gt=0).order_by('-tag_count')[:3]

    # Category list with counts (dynamic)
    categories = [
        {'name': 'Dryfruits', 'count': Product.objects.filter(category='DF').count(), 'url': 'Dryfruits'},
        {'name': 'Fishs', 'count': Product.objects.filter(category='FH').count(), 'url': 'Fish'},
        {'name': 'Fruits', 'count': Product.objects.filter(category='F').count(), 'url': 'Fruits'},
        {'name': 'Vegetables', 'count': Product.objects.filter(category='V').count(), 'url': 'Vegetable'},
        {'name': 'Meats', 'count': Product.objects.filter(category='M').count(), 'url': 'meat'},
    ]

    # Pagination - 9 per page (applied last)
    paginator = Paginator(products, 9)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    return render(request, 'shop/shop.html', {
        'products': products,
        'featured_products': featured_products,
        'categories': categories,
    })

@login_required
def cart(request):
    user_cart = get_cart(request)
    if user_cart:
        cart_items = user_cart.items.all()
        total = user_cart.total()
    else:
        cart_items = []
        total = 0
    return render(request, 'shop/cart.html', {'cart_items': cart_items, 'total': total})

@login_required
def chackout(request):
    user_cart = get_cart(request)
    if user_cart:
        cart_items = user_cart.items.all()
        total = user_cart.total()
    else:
        cart_items = []
        total = 0
    return render(request, 'shop/chackout.html', {'cart_items': cart_items, 'total': total})

class ProductDetails(View):
    def get(self, request, pk):
        product = Product.objects.get(pk=pk)
        return render(request, 'shop/product-detail.html', {
            'product': product
        })

def contact(request):
    return render(request, 'shop/contact.html')

def testimonial(request):
    return render(request, 'shop/testimonial.html')

def E_page(request):
    return render(request, 'shop/404.html')

def Profile(request):
    if request.method == 'POST':
        first_name = request.POST.get('firstname')
        last_name = request.POST.get('lastname')
        email = request.POST.get('email')
        address = request.POST.get('address')
        city = request.POST.get('city')
        country = request.POST.get('country')
        postcode = request.POST.get('postcode')
        mobile = request.POST.get('mobile')

        Profile = UserProfile(first_name=first_name, last_name=last_name, email=email, address=address, city=city, country=country, postcode=postcode, number=mobile)
        Profile.save()
        return render(request, 'shop/profile.html', {'userprofile': Profile})

    return render(request, 'shop/profile.html')

class userregistration(View):
    def get(self, request):
        form = UserRegForm()
        return render(request, 'shop/registration.html', {'form': form})

    def post(self, request):
        form = UserRegForm(request.POST)
        if form.is_valid():
            messages.success(request, 'Congratulations, User Created')
            form.save()
        return render(request, 'shop/registration.html', {'form': form})

# AJAX Views
@login_required
def add_to_cart(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        product = get_object_or_404(Product, id=product_id)
        cart = get_cart(request)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        cart_item.save()
        return JsonResponse({
            'success': True,
            'total_items': cart.items.count(),
            'cart_total': cart.total()
        })
    return JsonResponse({'success': False}, status=400)

@login_required
def update_cart_item(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')
        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        if action == 'increase':
            item.quantity += 1
        elif action == 'decrease' and item.quantity > 1:
            item.quantity -= 1
        item.save()
        return JsonResponse({
            'success': True,
            'new_quantity': item.quantity,
            'subtotal': item.subtotal(),
            'cart_total': item.cart.total()
        })
    return JsonResponse({'success': False}, status=400)

@login_required
def remove_from_cart(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        item_id = request.POST.get('item_id')
        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart = item.cart
        item.delete()
        return JsonResponse({
            'success': True,
            'cart_total': cart.total()
        })
    return JsonResponse({'success': False}, status=400)