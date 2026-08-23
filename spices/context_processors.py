from django.db.models import Sum
from .models import CartItem

def cart_processor(request):
    cart_count = 0
    if hasattr(request, 'user') and request.user.is_authenticated:
        result = CartItem.objects.filter(user=request.user).aggregate(total=Sum('quantity'))
        cart_count = result['total'] or 0
    else:
        session_cart = request.session.get('cart', {}) if hasattr(request, 'session') else {}
        cart_count = sum(int(q) for q in session_cart.values())

    return {
        'cart_count': cart_count
    }
