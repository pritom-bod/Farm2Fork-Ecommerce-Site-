# shop/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.views import LoginView
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
import logging

from .models import Product, UserProfile, Cart, CartItem, Order, OrderItem, Tag, ProductReview
from .forms import (
    UserRegForm, 
    LoginForm, 
    PassChangeForm, 
    UserProfileForm, 
    MyPasswordResetForm, 
    MySetPasswordForm
)

# Setup logging
logger = logging.getLogger(__name__)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_cart(request):
    """Get or create cart for authenticated user"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    return None


# ============================================================
# HOME & PRODUCT VIEWS
# ============================================================

class ProductView(View):
    """Home page view displaying products by category"""
    def get(self, request):
        try:
            allproducts = Product.objects.all()
            fruits = Product.objects.filter(category='F')
            vegetables = Product.objects.filter(category='V')
            meat = Product.objects.filter(category='M')
            bread = Product.objects.filter(category='B')
            
            context = {
                'allproducts': allproducts,
                'fruits': fruits,
                'vegetables': vegetables,
                'meat': meat,
                'bread': bread,
            }
            return render(request, 'shop/index.html', context)
        except Exception as e:
            logger.error(f"Error in ProductView: {str(e)}")
            messages.error(request, "An error occurred while loading products.")
            return render(request, 'shop/index.html', {})


def shop(request, data=None):
    """Shop page with filtering, searching, and pagination"""
    try:
        products = Product.objects.all()

        # Category filter from URL slug
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

        # Price filter
        price = request.GET.get('price')
        if price:
            try:
                products = products.filter(discounted_price__lte=int(price))
            except (ValueError, TypeError):
                pass

        # Status (tags) filter
        status_list = request.GET.getlist('status')
        if status_list:
            q = Q()
            for status in status_list:
                q |= Q(tags__name__iexact=status)
            products = products.filter(q).distinct()

        # Search filter
        search = request.GET.get('search')
        if search:
            products = products.filter(
                Q(title__icontains=search) | Q(descriptions__icontains=search)
            )

        # Sorting
        sort = request.GET.get('sort')
        if sort == 'popularity':
            products = products.order_by('-id')
        elif sort == 'organic':
            products = products.filter(tags__name__iexact='organic').distinct().order_by('title')
        elif sort == 'fantastic':
            products = products.order_by('-discounted_price')

        # Featured products
        featured_products = Product.objects.annotate(
            tag_count=Count('tags')
        ).filter(tag_count__gt=0).order_by('-tag_count')[:3]

        # Category list with counts
        categories = [
            {'name': 'Dryfruits', 'count': Product.objects.filter(category='DF').count(), 'url': 'Dryfruits'},
            {'name': 'Fishs', 'count': Product.objects.filter(category='FH').count(), 'url': 'Fish'},
            {'name': 'Fruits', 'count': Product.objects.filter(category='F').count(), 'url': 'Fruits'},
            {'name': 'Vegetables', 'count': Product.objects.filter(category='V').count(), 'url': 'Vegetable'},
            {'name': 'Meats', 'count': Product.objects.filter(category='M').count(), 'url': 'meat'},
        ]

        # Pagination
        paginator = Paginator(products, 9)
        page_number = request.GET.get('page')
        products = paginator.get_page(page_number)

        context = {
            'products': products,
            'featured_products': featured_products,
            'categories': categories,
        }
        return render(request, 'shop/shop.html', context)
    
    except Exception as e:
        logger.error(f"Error in shop view: {str(e)}")
        messages.error(request, "An error occurred while loading the shop.")
        return render(request, 'shop/shop.html', {})


class ProductDetails(View):
    """Product detail page with reviews and add to cart"""
    def get(self, request, pk):
        try:
            product = get_object_or_404(Product, pk=pk)
            
            # Get reviews (only from verified buyers)
            reviews = ProductReview.objects.filter(product=product).select_related('user', 'order')
            
            # Check if user has purchased this product and can review
            can_review = False
            user_has_reviewed = False
            user_order = None
            
            if request.user.is_authenticated:
                # Check if user bought this product
                user_order_item = OrderItem.objects.filter(
                    product=product,
                    order__user=request.user,
                    order__status='DELIVERED'
                ).first()
                
                if user_order_item:
                    can_review = True
                    user_order = user_order_item.order
                    
                    # Check if user already reviewed
                    user_has_reviewed = ProductReview.objects.filter(
                        product=product,
                        user=request.user,
                        order=user_order
                    ).exists()
            
            # Get featured products (products with high ratings)
            featured_products = Product.objects.annotate(
                avg_rating=Avg('reviews__rating'),
                review_count=Count('reviews')
            ).filter(review_count__gt=0).order_by('-avg_rating', '-review_count')[:6]
            
            # Get related products (same category)
            related_products = Product.objects.filter(
                category=product.category
            ).exclude(id=product.id)[:8]
            
            context = {
                'product': product,
                'reviews': reviews,
                'can_review': can_review,
                'user_has_reviewed': user_has_reviewed,
                'user_order': user_order,
                'featured_products': featured_products,
                'related_products': related_products,
            }
            return render(request, 'shop/product-detail.html', context)
        
        except Exception as e:
            logger.error(f"Error in product details: {str(e)}")
            messages.error(request, "Product not found.")
            return redirect('shop')
    
    def post(self, request, pk):
        """Handle review submission"""
        if not request.user.is_authenticated:
            messages.error(request, "Please login to post a review.")
            return redirect('login')
        
        try:
            product = get_object_or_404(Product, pk=pk)
            
            # Verify user purchased this product
            user_order_item = OrderItem.objects.filter(
                product=product,
                order__user=request.user,
                order__status='DELIVERED'
            ).first()
            
            if not user_order_item:
                messages.error(request, "You can only review products you have purchased.")
                return redirect('product_detail', pk=pk)
            
            # Check if already reviewed
            if ProductReview.objects.filter(
                product=product,
                user=request.user,
                order=user_order_item.order
            ).exists():
                messages.error(request, "You have already reviewed this product.")
                return redirect('product_detail', pk=pk)
            
            # Create review
            rating = int(request.POST.get('rating'))
            review_text = request.POST.get('review', '').strip()
            
            if not review_text or len(review_text) < 10:
                messages.error(request, "Review must be at least 10 characters long.")
                return redirect('product_detail', pk=pk)
            
            ProductReview.objects.create(
                product=product,
                user=request.user,
                order=user_order_item.order,
                rating=rating,
                review=review_text
            )
            
            messages.success(request, "Review submitted successfully!")
            return redirect('product_detail', pk=pk)
        
        except Exception as e:
            logger.error(f"Error submitting review: {str(e)}")
            messages.error(request, "An error occurred while submitting your review.")
            return redirect('product_detail', pk=pk)


# ============================================================
# CART VIEWS
# ============================================================

@login_required
def cart(request):
    """Display user's shopping cart"""
    try:
        user_cart = get_cart(request)
        if user_cart:
            cart_items = user_cart.items.all()
            total = user_cart.total()
        else:
            cart_items = []
            total = 0
        
        context = {
            'cart_items': cart_items,
            'total': total
        }
        return render(request, 'shop/cart.html', context)
    
    except Exception as e:
        logger.error(f"Error in cart view: {str(e)}")
        messages.error(request, "An error occurred while loading your cart.")
        return render(request, 'shop/cart.html', {'cart_items': [], 'total': 0})


# ============================================================
# CHECKOUT & ORDER VIEWS
# ============================================================

@login_required
def chackout(request):
    """Checkout page with order creation"""
    print("\n" + "="*60)
    print(f"CHECKOUT VIEW - Method: {request.method}")
    print(f"User: {request.user.username}")
    print("="*60 + "\n")
    
    try:
        # Get user cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = cart.items.select_related('product').all()
        subtotal = cart.total()
        
        print(f"Cart items count: {cart_items.count()}")
        print(f"Subtotal: ${subtotal}")
        
        # User profile (disabled temporarily)
        user_profile = None
        
        # Handle POST request (order submission)
        if request.method == 'POST':
            print("\n🔥 POST REQUEST RECEIVED!")
            print("POST Data:", dict(request.POST))
            
            if cart_items.count() == 0:
                messages.error(request, "Your cart is empty!")
                return redirect('cart')
            
            try:
                # Get form data
                first_name = request.POST.get('first_name', '').strip()
                last_name = request.POST.get('last_name', '').strip()
                company_name = request.POST.get('company_name', '').strip()
                email = request.POST.get('email', '').strip()
                phone = request.POST.get('phone', '').strip()
                address = request.POST.get('address', '').strip()
                city = request.POST.get('city', '').strip()
                country = request.POST.get('country', '').strip()
                postcode = request.POST.get('postcode', '').strip()
                shipping_method = request.POST.get('shipping_method', 'FREE')
                payment_method = request.POST.get('payment_method')
                notes = request.POST.get('notes', '').strip()
                
                print(f"\n📋 Order Details:")
                print(f"  Name: {first_name} {last_name}")
                print(f"  Email: {email}")
                print(f"  Payment: {payment_method}")
                print(f"  Shipping: {shipping_method}")
                
                # Validate required fields
                if not all([first_name, last_name, email, phone, address, city, country, postcode, payment_method]):
                    messages.error(request, "Please fill in all required fields!")
                    raise ValueError("Missing required fields")
                
                # Calculate shipping cost
                shipping_costs = {'FREE': 0.00, 'FLAT': 15.00, 'LOCAL': 8.00}
                shipping_cost = shipping_costs.get(shipping_method, 0.00)
                total = float(subtotal) + shipping_cost
                
                # Generate order number
                order_number = f"ORD{get_random_string(10).upper()}"
                
                print(f"\n💰 Order Calculation:")
                print(f"  Subtotal: ${subtotal}")
                print(f"  Shipping: ${shipping_cost}")
                print(f"  Total: ${total}")
                print(f"  Order Number: {order_number}")
                
                # Create Order
                with transaction.atomic():
                    order = Order.objects.create(
                        user=request.user,
                        order_number=order_number,
                        first_name=first_name,
                        last_name=last_name,
                        company_name=company_name,
                        email=email,
                        phone=phone,
                        address=address,
                        city=city,
                        country=country,
                        postcode=postcode,
                        shipping_method=shipping_method,
                        shipping_cost=shipping_cost,
                        payment_method=payment_method,
                        subtotal=subtotal,
                        total=total,
                        notes=notes,
                        status='PENDING'
                    )
                    
                    print(f"✅ Order created: {order.id}")
                    
                    # Create Order Items
                    for item in cart_items:
                        order_item = OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            quantity=item.quantity,
                            price=item.product.discounted_price,
                            subtotal=item.subtotal()
                        )
                        print(f"  - Added: {order_item}")
                    
                    # Clear cart
                    cart_items.delete()
                    print("🛒 Cart cleared")
                
                print(f"\n🎉 ORDER PLACED SUCCESSFULLY!")
                print(f"Redirecting to: order_confirmation/{order_number}")
                print("="*60 + "\n")
                
                messages.success(request, f"Order placed successfully! Order Number: {order_number}")
                return redirect('order_confirmation', order_number=order_number)
            
            except Exception as e:
                print(f"\n❌ ERROR creating order: {str(e)}")
                import traceback
                traceback.print_exc()
                messages.error(request, f"Error: {str(e)}")
        
        # GET request - display form
        context = {
            'cart_items': cart_items,
            'subtotal': subtotal,
            'user_profile': user_profile,
        }
        
        return render(request, 'shop/chackout.html', context)
    
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"Error: {str(e)}")
        return render(request, 'shop/chackout.html', {
            'cart_items': [],
            'subtotal': 0,
            'user_profile': None,
        })


@login_required
def order_confirmation(request, order_number):
    """Order confirmation page"""
    try:
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        order_items = order.items.all()
        
        context = {
            'order': order,
            'order_items': order_items,
        }
        return render(request, 'shop/order-confirmation.html', context)
    
    except Exception as e:
        logger.error(f"Error in order confirmation: {str(e)}")
        messages.error(request, "Order not found.")
        return redirect('profile')


@login_required
def order_detail(request, order_number):
    """Order detail page"""
    try:
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        order_items = order.items.all()
        
        context = {
            'order': order,
            'order_items': order_items,
        }
        return render(request, 'shop/order-detail.html', context)
    
    except Exception as e:
        logger.error(f"Error in order detail: {str(e)}")
        messages.error(request, "Order not found.")
        return redirect('profile')


# ============================================================
# USER PROFILE
# ============================================================

@login_required
def profile(request):
    """User profile and dashboard"""
    try:
        # Get or create user profile - WITH ERROR HANDLING
        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            user_profile = UserProfile.objects.create(
                user=request.user,
                first_name=request.user.first_name or '',
                last_name=request.user.last_name or '',
                email=request.user.email or '',
                phone='',
                address='',
                city='',
                country='Bangladesh',
                postcode=''
            )
        
        # Get user's orders
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        
        # Calculate statistics
        total_orders = orders.count()
        pending_orders = orders.filter(status='PENDING').count()
        completed_orders = orders.filter(status='DELIVERED').count()
        total_spent = orders.filter(
            status__in=['PROCESSING', 'SHIPPED', 'DELIVERED']
        ).aggregate(total=Sum('total'))['total'] or 0
        
        if request.method == 'POST':
            try:
                first_name = request.POST.get('first_name', '').strip()
                last_name = request.POST.get('last_name', '').strip()
                email = request.POST.get('email', '').strip()
                phone = request.POST.get('phone', '').strip()
                address = request.POST.get('address', '').strip()
                city = request.POST.get('city', '').strip()
                country = request.POST.get('country', '').strip()
                postcode = request.POST.get('postcode', '').strip()
                
                # Update profile
                user_profile.first_name = first_name
                user_profile.last_name = last_name
                user_profile.email = email
                user_profile.phone = phone
                user_profile.address = address
                user_profile.city = city
                user_profile.country = country
                user_profile.postcode = postcode
                
                # Handle profile image
                if 'profile_image' in request.FILES:
                    user_profile.profile_image = request.FILES['profile_image']
                
                user_profile.save()
                
                # Update user's first name, last name, email
                request.user.first_name = first_name
                request.user.last_name = last_name
                request.user.email = email
                request.user.save()
                
                logger.info(f"Profile updated for user {request.user.username}")
                messages.success(request, "Profile updated successfully!")
                return redirect('profile')
            
            except Exception as e:
                logger.error(f"Error updating profile: {str(e)}")
                messages.error(request, "An error occurred while updating your profile.")
                return redirect('profile')
        
        context = {
            'user_profile': user_profile,
            'orders': orders[:5],
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'total_spent': total_spent,
        }
        return render(request, 'shop/profile.html', context)
    
    except Exception as e:
        logger.error(f"Error in profile view: {str(e)}")
        messages.error(request, "An error occurred while loading your profile.")
        return render(request, 'shop/profile.html', {})


# ============================================================
# AUTHENTICATION VIEWS
# ============================================================

class userregistration(View):
    """User registration view"""
    def get(self, request):
        form = UserRegForm()
        return render(request, 'shop/registration.html', {'form': form})

    def post(self, request):
        form = UserRegForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Congratulations! Your account has been created successfully.')
                logger.info(f"New user registered: {form.cleaned_data.get('username')}")
                return redirect('login')
            except Exception as e:
                logger.error(f"Error during registration: {str(e)}")
                messages.error(request, "An error occurred during registration.")
        return render(request, 'shop/registration.html', {'form': form})


class CustomLoginView(LoginView):
    """Custom login view with redirect message"""
    def get(self, request, *args, **kwargs):
        if 'next' in request.GET:
            messages.info(request, 'Please login to access that page.')
        return super().get(request, *args, **kwargs)


# ============================================================
# STATIC PAGES
# ============================================================

def contact(request):
    """Contact page"""
    return render(request, 'shop/contact.html')


def testimonial(request):
    """Testimonial page"""
    return render(request, 'shop/testimonial.html')


def E_page(request):
    """404 error page"""
    return render(request, 'shop/404.html')


# ============================================================
# AJAX CART OPERATIONS
# ============================================================

def add_to_cart(request):
    """Add product to cart via AJAX"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            if not request.user.is_authenticated:
                return JsonResponse({'success': False, 'redirect': '/account/Login/'})
            
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
        
        except Exception as e:
            logger.error(f"Error adding to cart: {str(e)}")
            return JsonResponse({'success': False, 'error': 'An error occurred'}, status=500)
    
    return JsonResponse({'success': False}, status=400)


def update_cart_item(request):
    """Update cart item quantity via AJAX"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            if not request.user.is_authenticated:
                return JsonResponse({'success': False, 'redirect': '/account/Login/'})
            
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
        
        except Exception as e:
            logger.error(f"Error updating cart item: {str(e)}")
            return JsonResponse({'success': False, 'error': 'An error occurred'}, status=500)
    
    return JsonResponse({'success': False}, status=400)


def remove_from_cart(request):
    """Remove item from cart via AJAX"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            if not request.user.is_authenticated:
                return JsonResponse({'success': False, 'redirect': '/account/Login/'})
            
            item_id = request.POST.get('item_id')
            item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            cart = item.cart
            item.delete()
            
            return JsonResponse({
                'success': True,
                'cart_total': cart.total()
            })
        
        except Exception as e:
            logger.error(f"Error removing from cart: {str(e)}")
            return JsonResponse({'success': False, 'error': 'An error occurred'}, status=500)
    
    return JsonResponse({'success': False}, status=400)
@login_required
def add_to_cart_view(request, pk):
    """Standard POST add to cart (not AJAX)"""
    product = get_object_or_404(Product, pk=pk)
    cart, created = Cart.objects.get_or_create(user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    messages.success(request, f"{product.title} added to cart!")
    return redirect('product_detail', pk=pk)
