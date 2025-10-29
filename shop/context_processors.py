from .models import Cart

def cart_item_count(request):
    count = 0
    if request.user.is_authenticated:
        try:
            cart, created = Cart.objects.get_or_create(user=request.user)
            count = sum(item.quantity for item in cart.items.all())
        except:
            pass  # No cart or some error, keep count 0
    return {'cart_item_count': count}
