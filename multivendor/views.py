from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Seller
from .forms import SellerRegisterForm, SellerLoginForm, SellerProductForm, SellerProfileForm
from shop.models import Product, OrderItem, Order, ProductQuestion
from django.contrib.auth.decorators import login_required
from django.utils import timezone

def seller_register(request):
    if request.method == 'POST':
        form = SellerRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            Seller.objects.create(
                user=user,
                shop_name=form.cleaned_data['shop_name'],
                bio=form.cleaned_data['bio'],
                shop_logo=form.cleaned_data.get('shop_logo')
            )
            messages.success(request, "Seller account created! Login now.")
            return redirect('multivendor:seller_login')
    else:
        form = SellerRegisterForm()
    return render(request, 'multivendor/seller_register.html', {'form': form})

def seller_login(request):
    if request.user.is_authenticated and hasattr(request.user, 'seller_account'):
        return redirect('multivendor:seller_dashboard')
    if request.method == 'POST':
        form = SellerLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            try:
                seller = user.seller_account
            except Seller.DoesNotExist:
                messages.error(request, "No seller account found for this user.")
                return render(request, 'multivendor/seller_login.html', {'form': form})
            login(request, user)
            return redirect('multivendor:seller_dashboard')
    else:
        form = SellerLoginForm()
    return render(request, 'multivendor/seller_login.html', {'form': form})

@login_required
def seller_logout(request):
    logout(request)
    return redirect('multivendor:seller_login')

@login_required
def seller_dashboard(request):
    seller = get_object_or_404(Seller, user=request.user)
    products = Product.objects.filter(seller=seller)
    product_ids = products.values_list('id', flat=True)
    order_items = OrderItem.objects.filter(product_id__in=product_ids)
    orders = set(oi.order for oi in order_items)
    earnings = sum(o.total for o in orders if hasattr(o, 'total') and getattr(o, 'status', None) == 'DELIVERED')
    order_count = len(orders)
    return render(request, 'multivendor/seller_dashboard.html', {
        'seller': seller,
        'products': products,
        'orders': orders,
        'earnings': earnings,
        'order_count': order_count
    })

@login_required
def seller_add_product(request):
    seller = get_object_or_404(Seller, user=request.user)
    if request.method == 'POST':
        form = SellerProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = seller
            product.save()
            form.save_m2m()
            messages.success(request, "Product added successfully.")
            return redirect('multivendor:seller_dashboard')
    else:
        form = SellerProductForm()
    return render(request, 'multivendor/seller_add_product.html', {'form': form})

@login_required
def seller_orders(request):
    seller = get_object_or_404(Seller, user=request.user)
    products = Product.objects.filter(seller=seller)
    product_ids = products.values_list('id', flat=True)
    order_items = OrderItem.objects.filter(product_id__in=product_ids)
    orders = set(oi.order for oi in order_items)
    return render(request, 'multivendor/seller_orders.html', {
        'orders': orders
    })


@login_required
def seller_profile(request):
    seller = get_object_or_404(Seller, user=request.user)
    if request.method == 'POST':
        form = SellerProfileForm(request.POST, request.FILES, instance=seller)  # You need to create SellerProfileForm
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('multivendor:seller_profile')
    else:
        form = SellerProfileForm(instance=seller)
    return render(request, 'multivendor/seller_profile.html', {'form': form, 'seller': seller})


@login_required
def seller_orders(request):
    seller = get_object_or_404(Seller, user=request.user)
    products = Product.objects.filter(seller=seller)
    product_ids = products.values_list('id', flat=True)
    order_items = OrderItem.objects.filter(product_id__in=product_ids)
    orders = list(set(oi.order for oi in order_items))

    if request.method == "POST":
        order_id = request.POST.get("order_id")
        new_status = request.POST.get("status")
        # FIX: use .filter().distinct().first() not get_object_or_404
        order = Order.objects.filter(id=order_id, items__product__seller=seller).distinct().first()
        if not order:
            messages.error(request, "Order not found.")
            return redirect('multivendor:seller_orders')

        if new_status in ["PENDING", "ON_THE_WAY", "DELIVERED", "CANCELLED"]:
            order.status = new_status
            order.save()
            messages.success(request, f"Order status updated to {new_status}.")
        else:
            messages.error(request, "Invalid status selected.")
        return redirect('multivendor:seller_orders')

    return render(request, 'multivendor/seller_orders.html', {
        'orders': orders
    })


@login_required
def seller_all_products(request):
    seller = get_object_or_404(Seller, user=request.user)
    products = Product.objects.filter(seller=seller)
    return render(request, 'multivendor/seller_all_products.html', {
        'products': products,
        'seller': seller,
    })

@login_required
def seller_product_questions(request):
    seller = get_object_or_404(Seller, user=request.user)
    questions = ProductQuestion.objects.filter(product__seller=seller)
    unanswered_questions = questions.filter(is_answered=False)
    answered_questions = questions.filter(is_answered=True)
    context = {
        'unanswered_questions': unanswered_questions,
        'answered_questions': answered_questions
    }
    return render(request, 'multivendor/seller_questions.html', context)

@login_required
def seller_answer_question(request, question_id):
    # Get the seller object from current user
    seller = get_object_or_404(Seller, user=request.user)
    # Get the ProductQuestion and check it's this seller's product
    question = get_object_or_404(ProductQuestion, id=question_id, product__seller=seller)
    if request.method == 'POST':
        answer = request.POST.get('answer', '').strip()
        if answer:
            question.answer = answer
            question.is_answered = True
            question.answered_by = request.user
            question.answered_at = timezone.now()
            question.save()
            messages.success(request, 'Answer posted successfully!')
            return redirect('multivendor:seller_product_questions')
        else:
            messages.error(request, 'Please provide an answer.')
    # GET request: show answer page
    return render(request, 'multivendor/seller_answer_question.html', {
        'seller': seller,
        'question': question
    })