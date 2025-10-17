from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
from .models import Product, UserProfile, Cart, CartItem, Tag, Order, OrderItem
from django.db.models import Sum
from django.views import View
from django.contrib import messages
from .forms import UserRegForm, LoginForm, PassChangeForm, ReviewForm, ProfileForm, OrderForm, Review
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.db import IntegrityError

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
        
        # Fetch bestseller products based on total quantity sold
        bestseller_products = Product.objects.annotate(
            total_sold=Sum('orderitem__quantity')
        ).order_by('-total_sold')[:6]  # Top 6 bestselling products
        
        # Fetch latest reviews for testimonials
        testimonials = Review.objects.select_related('user').order_by('-created_at')[:3]  # Top 3 recent reviews

        return render(request, 'shop/index.html', {
            'allproducts': allproducts,
            'fruits': fruits,
            'vegetables': vegetables,
            'meat': meat,
            'bread': bread,
            'bestseller_products': bestseller_products,
            'testimonials': testimonials,
        })

# ... (rest of the views remain unchanged)

def shop(request, data=None):
    products = Product.objects.all()
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
    price = request.GET.get('price')
    if price:
        try:
            products = products.filter(discounted_price__lte=int(price))
        except ValueError:
            pass
    status_list = request.GET.getlist('status')
    if status_list:
        q = Q()
        for status in status_list:
            q |= Q(tags__name__iexact=status)
        products = products.filter(q).distinct()
    search = request.GET.get('search')
    if search:
        products = products.filter(Q(title__icontains=search) | Q(descriptions__icontains=search))
    sort = request.GET.get('sort')
    if sort == 'popularity':
        products = products.order_by('-id')
    elif sort == 'organic':
        products = products.filter(tags__name__iexact='organic').distinct().order_by('title')
    elif sort == 'fantastic':
        products = products.order_by('-discounted_price')
    featured_products = Product.objects.annotate(tag_count=Count('tags')).filter(tag_count__gt=0).order_by('-tag_count')[:3]
    categories = [
        {'name': 'Dryfruits', 'count': Product.objects.filter(category='DF').count(), 'url': 'Dryfruits'},
        {'name': 'Fishs', 'count': Product.objects.filter(category='FH').count(), 'url': 'Fish'},
        {'name': 'Fruits', 'count': Product.objects.filter(category='F').count(), 'url': 'Fruits'},
        {'name': 'Vegetables', 'count': Product.objects.filter(category='V').count(), 'url': 'Vegetable'},
        {'name': 'Meats', 'count': Product.objects.filter(category='M').count(), 'url': 'meat'},
    ]
    paginator = Paginator(products, 9)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    return render(request, 'shop/shop.html', {
        'products': products,
        'featured_products': featured_products,
        'categories': categories,
    })

def cart(request):
    if not request.user.is_authenticated:
        return render(request, 'shop/empty_cart.html')
    user_cart = get_cart(request)
    if user_cart:
        cart_items = user_cart.items.all()
        total = user_cart.total()
    else:
        cart_items = []
        total = 0
    return render(request, 'shop/cart.html', {'cart_items': cart_items, 'total': total})


def cart_item_count(request):
    if request.user.is_authenticated:
        try:
            user_cart = Cart.objects.get(user=request.user)
            return {'cart_item_count': user_cart.items.count()}
        except Cart.DoesNotExist:
            return {'cart_item_count': 0}
    return {'cart_item_count': 0}

@login_required
def checkout(request):
    cart = get_cart(request)
    if not cart or not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                user=request.user,
                total_amount=cart.total(),
                shipping_address=form.cleaned_data['shipping_address'],
                payment_method=form.cleaned_data['payment_method']
            )
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.discounted_price
                )
            cart.items.all().delete()
            return redirect('order_success', order_id=order.id)
    else:
        form = OrderForm()
    return render(request, 'shop/checkout.html', {'cart_items': cart.items.all(), 'total': cart.total(), 'form': form})

class ProductDetails(View):
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        has_purchased = False
        if request.user.is_authenticated:
            has_purchased = OrderItem.objects.filter(order__user=request.user, product=product).exists()
        reviews = product.reviews.all()
        form = ReviewForm() if has_purchased else None
        return render(request, 'shop/product-detail.html', {
            'product': product,
            'has_purchased': has_purchased,
            'reviews': reviews,
            'form': form
        })

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        subject = f'New Contact Form Submission from {name}'
        from_email = email
        to_email = ['pritomsarker406@gmail.com']  # Replace with your specific email
        try:
            send_mail(
                subject,
                message,
                from_email,
                to_email,
                fail_silently=False,
            )
            messages.success(request, 'Your message has been sent successfully!')
        except Exception as e:
            messages.error(request, f'Failed to send message: {str(e)}')
        return redirect('contact')
    return render(request, 'shop/contact.html')

def testimonial(request):
    return render(request, 'shop/testimonial.html')

def E_page(request):
    return render(request, 'shop/404.html')

@login_required
def profile(request):
    # Check if a UserProfile already exists for the user
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        # If profile exists, redirect to my_account for editing
        messages.info(request, 'Profile already exists. You can edit it in My Account.')
        return redirect('my_account')
    except UserProfile.DoesNotExist:
        # No profile exists, proceed to create one
        if request.method == 'POST':
            form = ProfileForm(request.POST)
            if form.is_valid():
                try:
                    user_profile = form.save(commit=False)
                    user_profile.user = request.user
                    user_profile.save()
                    messages.success(request, 'Profile created successfully!')
                    return redirect('my_account')
                except IntegrityError:
                    form.add_error('number', 'This phone number is already in use.')
                    form.add_error('email', 'This email is already in use.')
            # If form is invalid or IntegrityError occurs, re-render with errors
            return render(request, 'shop/profile.html', {'form': form})
        else:
            form = ProfileForm()
        return render(request, 'shop/profile.html', {'form': form})

@login_required
def my_account(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return redirect('profile')
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('my_account')
            except IntegrityError:
                form.add_error('number', 'This phone number is already in use.')
                form.add_error('email', 'This email is already in use.')
            return render(request, 'shop/my_account.html', {'form': form, 'orders': orders})
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'shop/my_account.html', {'form': form, 'orders': orders})

class userregistration(View):
    def get(self, request):
        form = UserRegForm()
        return render(request, 'shop/registration.html', {'form': form})

    def post(self, request):
        form = UserRegForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Congratulations, User Created')
            return redirect('login')
        return render(request, 'shop/registration.html', {'form': form})

def add_to_cart(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'You have to login first.', 'redirect': '/account/Login/'})
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

def update_cart_item(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'You have to login first.', 'redirect': '/account/Login/'})
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

def remove_from_cart(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'You have to login first.', 'redirect': '/account/Login/'})
        item_id = request.POST.get('item_id')
        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart = item.cart
        item.delete()
        return JsonResponse({
            'success': True,
            'cart_total': cart.total()
        })
    return JsonResponse({'success': False}, status=400)

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'shop/order_success.html', {'order': order})

@login_required
def submit_review(request, pk):
    product = get_object_or_404(Product, pk=pk)
    has_purchased = OrderItem.objects.filter(order__user=request.user, product=product).exists()
    if not has_purchased:
        messages.error(request, 'You can only review purchased products.')
        return redirect('productdetails', pk=pk)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'rating': review.rating,
                    'comment': review.comment,
                    'user': review.user.username,
                    'average_rating': product.average_rating(),
                })
            messages.success(request, 'Review submitted successfully!')
            return redirect('productdetails', pk=pk)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return redirect('productdetails', pk=pk)