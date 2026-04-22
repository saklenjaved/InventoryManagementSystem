def accounts_user(request):
    cart = request.session.get('cart', {})    # get Cart from session
    cart_count = 0
    for qty in cart.values():
        try:
            cart_count += int(qty)              # convert integer of each quantity
        except (TypeError, ValueError): 
            continue
    return {
        'accounts_user': getattr(request, 'accounts_user', None),     # if account_user in request then return else none
        'cart_count': cart_count,                                       # sent data to template
    }
