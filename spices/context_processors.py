def cart_processor(request):
    cart = request.session.get('cart', {})
    cart_count = sum(item.get('quantity', 1) for item in cart.values()) if isinstance(cart, dict) else 0
    return {
        'cart_count': cart_count
    }
