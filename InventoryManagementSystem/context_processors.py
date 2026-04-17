def accounts_user(request):
    cart = request.session.get('cart', {})
    cart_count = 0
    for qty in cart.values():
        try:
            cart_count += int(qty)
        except (TypeError, ValueError):
            continue
    return {
        'accounts_user': getattr(request, 'accounts_user', None),
        'cart_count': cart_count,
    }
