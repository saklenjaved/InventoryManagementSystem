from functools import wraps
from urllib.parse import urlencode

from accounts.models import LoginActivity, User, UserProfile
from django.contrib import messages
from django.db import transaction
from django.db.models import DecimalField, ExpressionWrapper, F
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_http_methods
from django.views.generic import DeleteView, ListView
from django.views.generic.edit import CreateView, UpdateView

from .forms import CategoryForm, ProductForm, PurchaseForm, SaleForm
from .models import Category, Product, Purchase, Sale


def inventory_admin_required(view_func):
    @wraps(view_func)                                       # decorator that wrap function view and checks user login and admin.role
    def wrapper(request, *args, **kwargs):
        user = getattr(request, 'accounts_user', None)
        if not user:
            login_url = reverse('accounts:login')
            query = urlencode({'next': request.get_full_path()})
            return redirect(f'{login_url}?{query}')
        if user.role != 'admin':
            messages.warning(
                request,
                'Inventory tools are available to administrators only.',
            )
            return redirect('shop_home')
        return view_func(request, *args, **kwargs)

    return wrapper


class InventoryAdminRequiredMixin:
    """Require signed-in accounts.User with role admin."""

    def dispatch(self, request, *args, **kwargs):                           # mixin that dispatch with class based views and checks admin role
        user = getattr(request, 'accounts_user', None)
        if not user:
            login_url = reverse('accounts:login')
            query = urlencode({'next': request.get_full_path()})
            return redirect(f'{login_url}?{query}')
        if user.role != 'admin':
            messages.warning(
                request,
                'Inventory tools are available to administrators only.',
            )
            return redirect('shop_home')
        return super().dispatch(request, *args, **kwargs)


class LoggedInAccountsMixin:
    """Any signed-in user (shop purchases / sales as customer)."""

    def dispatch(self, request, *args, **kwargs):
        if not getattr(request, 'accounts_user', None):
            login_url = reverse('accounts:login')
            query = urlencode({'next': request.get_full_path()})
            return redirect(f'{login_url}?{query}')
        return super().dispatch(request, *args, **kwargs)


def _get_cart(request):
    # get cart from user 
    return request.session.get('cart', {})


def _save_cart(request, cart):
    # saves changed cart in session
    request.session['cart'] = cart
    request.session.modified = True


def _cart_rows(cart):
    product_ids = [int(pid) for pid in cart.keys() if str(pid).isdigit()]       # listing cart ID's
    if not product_ids:
        return []
    products = Product.objects.select_related('category').filter(pk__in=product_ids)      # fetch products from DB
    product_map = {str(p.pk): p for p in products}          # create dict for fast look up and easily find products
    rows = []                                               # create final list and store cart items
    for pid, qty in cart.items():               # process with each products
        product = product_map.get(str(pid))                 # get products by their ID
        if not product:
            continue
        quantity = int(qty)             # convert string into integer
        line_total = product.price * quantity           # calculate the total price of one product
        rows.append(
            {
                'product': product,
                'quantity': quantity,
                'unit_price': product.price,
                'line_total': line_total,
                }
        )
    return rows


def shop_home(request):
    """Public storefront: browse products without logging in."""
    categories = Category.objects.all().order_by('name')       # get all categories and sorting them by name
    products = Product.objects.select_related('category').order_by('category__name', 'name')    # sorintg them by cateories, 1st cat_name and p.name
    cat_param = request.GET.get('category')     # get cat.id
    if cat_param and str(cat_param).isdigit():      # checks value, if category is valid number then continue 
        products = products.filter(category_id=int(cat_param))      # filters the product category wise
    products = list(products)      # create list 
    cart = _get_cart(request)           
    shop_cards = []             # store final data
    for p in products:  
        shop_cards.append(
            {
                'product': p,
                'in_cart_qty': int(cart.get(str(p.pk), 0)),
            }
        )
    return render(
        request,
        'inventory/shop.html',
        {
            'categories': categories,
            'shop_cards': shop_cards,
            'active_category': int(cat_param) if cat_param and str(cat_param).isdigit() else None,
        },
    )


@require_http_methods(['POST'])
def cart_add(request, product_id):
    product = Product.objects.filter(pk=product_id).first()     # get product from ID
    if not product:
        messages.error(request, 'Product not found.')
        return redirect('shop_home')
    if product.quantity <= 0:
        messages.error(request, 'This product is out of stock.')
        return redirect(request.POST.get('next') or 'shop_home')
    try:
        qty = int(request.POST.get('quantity', 1))        # user select quantity
    except (TypeError, ValueError):    
        qty = 1                                         # default 1 quantity select
    qty = max(1, qty)                           
    cart = _get_cart(request)               # get cart from session
    key = str(product.pk)           
    new_qty = int(cart.get(key, 0)) + qty       # calculate new quantity with old quantity
    if new_qty > product.quantity:                 
        new_qty = product.quantity
        messages.warning(request, f'Only {product.quantity} units available.')
    cart[key] = new_qty
    _save_cart(request, cart)
    messages.success(request, f'{product.name} added to cart.')
    return redirect(request.POST.get('next') or 'shop_home')


def cart_detail(request):
    rows = _cart_rows(_get_cart(request))      # convert in cart in rows format
    grand_total = sum((r['line_total'] for r in rows), 0)      # total sum of all products 
    return render(
        request,
        'inventory/cart.html',
        {                                   # render page in template
            'rows': rows,
            'grand_total': grand_total,
        },
    )


@require_http_methods(['POST'])
def cart_update(request, product_id):
    cart = _get_cart(request)       
    key = str(product_id)        # convert p.id in string
    if key not in cart:
        return redirect('inventory:cart')
    try:
        qty = int(request.POST.get('quantity', 1))         # quantity users added
    except (TypeError, ValueError):
        qty = 1
    product = Product.objects.filter(pk=product_id).first()      # checks products exist or not
    if not product:                 
        cart.pop(key, None)                 # if not, so remove from cart
        _save_cart(request, cart)
        messages.info(request, 'Product removed from cart because it no longer exists.')
        return redirect('inventory:cart')
    if qty <= 0:
        cart.pop(key, None)
        messages.info(request, 'Item removed from cart.')
    else:
        if qty > product.quantity:
            qty = product.quantity
            messages.warning(request, f'Only {product.quantity} units available.')
        cart[key] = qty             # update and save
    _save_cart(request, cart)
    return redirect('inventory:cart')


@require_http_methods(['POST'])
def cart_remove(request, product_id):
    cart = _get_cart(request)
    cart.pop(str(product_id), None)             # removes item from cart
    _save_cart(request, cart)
    messages.info(request, 'Item removed from cart.')
    return redirect('inventory:cart')


@require_http_methods(['GET', 'POST'])
def cart_checkout(request):
    if not getattr(request, 'accounts_user', None):             # if user not login then redirect login
        login_url = reverse('accounts:login')
        query = urlencode({'next': reverse('inventory:cart_checkout')})
        return redirect(f'{login_url}?{query}')

    profile, _ = UserProfile.objects.get_or_create(
        user=request.accounts_user,                     # get user profile
        defaults={                      
            'first_name': request.accounts_user.username,
            'last_name': '',
            'phone': '',
            'address': '',
            'city': '',
            'state': '',
        },
    )
    address_parts = [profile.address, profile.city, profile.state]
    delivery_address = ', '.join([part for part in address_parts if part])    # combine address, city, state
    if not delivery_address:
        messages.warning(
            request,
            'Please update your address in profile before checkout.',
        )
        return redirect('accounts:profile')

    rows = _cart_rows(_get_cart(request))           # get cart data in rows        
    if not rows:                                
        messages.warning(request, 'Your cart is empty.')
        return redirect('inventory:cart')

    grand_total = sum((r['line_total'] for r in rows), 0)               # total calculate
    if request.method == 'POST':
        if request.POST.get('confirm_address') != 'yes':                # user confirms and select checkbox if addrress are confirm
            messages.error(request, 'Please confirm this delivery address to place the order.')
            return redirect('inventory:cart_checkout')
        with transaction.atomic():                  # all cart product orders are works together.  if one product is false, all oproducts order can cancel
            for row in rows:
                product = Product.objects.select_for_update().get(pk=row['product'].pk)    # locks the DB row
                qty = row['quantity']       # quantity of user ordered                                            # whenever this product can not buyed, nothing else products can changed.
                if product.quantity < qty:
                    messages.error(
                        request,
                        f'Not enough stock for {product.name}. Available: {product.quantity}.',
                    )
                    return redirect('inventory:cart')
                product.quantity -= qty
                product.save()
                Sale.objects.create(
                    product=product,                # saved order in DB
                    quantity=qty,
                    price=product.price,
                    customer=request.accounts_user,
                )
        _save_cart(request, {})             # save cart
        messages.success(request, f'Checkout complete. Total amount: {grand_total}')
        return redirect('inventory:sale_list')

    return render(
        request,
        'inventory/checkout.html',
        {
            'rows': rows,
            'grand_total': grand_total,
            'profile': profile,
            'delivery_address': delivery_address,
        },
    )


@inventory_admin_required         # admin login required for opens dashboard
def dashboard(request):
    products = list(Product.objects.select_related('category').all())       # lists of all products
    low_stock = [p for p in products if p.quantity <= 5]                # low stock products when there stock are 5 or lower  
    recent_purchases = Purchase.objects.select_related('product', 'buyer').order_by('-date', '-id')[:5]
    recent_sales = Sale.objects.select_related('product', 'customer').order_by('-date', '-id')[:5]
    recent_logins = LoginActivity.objects.select_related('user').order_by('-login_at', '-id')[:10]
    return render(
        request,
        'inventory/dashboard.html',
        {
            'product_count': len(products),
            'category_count': Category.objects.count(),
            'registered_user_count': User.objects.count(),
            'low_stock': low_stock[:10],
            'recent_purchases': recent_purchases,
            'recent_sales': recent_sales,
            'recent_logins': recent_logins,
        },
    )


class CategoryListView(InventoryAdminRequiredMixin, ListView):
    model = Category                                        # ListView = built-in djando view
    template_name = 'inventory/category_list.html'         # show category list for only admin 
    context_object_name = 'categories'


class CategoryCreateView(InventoryAdminRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'inventory/category_form.html'              # for new category create 
    success_url = reverse_lazy('inventory:category_list')

    def form_valid(self, form):
        messages.success(self.request, 'Category created.')
        return super().form_valid(form)             # super() calls the parent class method 


class CategoryUpdateView(InventoryAdminRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'inventory/category_form.html'
    success_url = reverse_lazy('inventory:category_list')

    def form_valid(self, form):
        messages.success(self.request, 'Category updated.')
        return super().form_valid(form)


class CategoryDeleteView(InventoryAdminRequiredMixin, DeleteView):
    model = Category
    template_name = 'inventory/category_confirm_delete.html'
    success_url = reverse_lazy('inventory:category_list')

    def form_valid(self, form):
        messages.success(self.request, 'Category deleted.')
        return super().form_valid(form)


class ProductListView(InventoryAdminRequiredMixin, ListView):
    model = Product
    template_name = 'inventory/product_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.select_related('category').all()


class ProductCreateView(InventoryAdminRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    success_url = reverse_lazy('inventory:product_list')

    def form_valid(self, form):
        messages.success(self.request, 'Product created.')
        return super().form_valid(form)


class ProductUpdateView(InventoryAdminRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    success_url = reverse_lazy('inventory:product_list')

    def form_valid(self, form):
        messages.success(self.request, 'Product updated.')
        return super().form_valid(form)


class ProductDeleteView(InventoryAdminRequiredMixin, DeleteView):
    model = Product
    template_name = 'inventory/product_confirm_delete.html'
    success_url = reverse_lazy('inventory:product_list')

    def form_valid(self, form):
        messages.success(self.request, 'Product deleted.')
        return super().form_valid(form)


class PurchaseListView(InventoryAdminRequiredMixin, ListView):
    model = Purchase
    template_name = 'inventory/purchase_list.html'
    context_object_name = 'purchases'

    def get_queryset(self):
        return Purchase.objects.select_related('product', 'buyer').order_by('-date', '-id')


class PurchaseCreateView(InventoryAdminRequiredMixin, CreateView):
    model = Purchase
    form_class = PurchaseForm
    template_name = 'inventory/purchase_form.html'
    success_url = reverse_lazy('inventory:purchase_list')

    def form_valid(self, form):
        purchase = form.save(commit=False)
        purchase.buyer = self.request.accounts_user
        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=purchase.product_id)
            product.quantity += purchase.quantity
            product.save()
            purchase.save()
        messages.success(self.request, 'Purchase recorded and stock updated.')
        return redirect(self.success_url)


class SaleListView(LoggedInAccountsMixin, ListView):
    model = Sale
    template_name = 'inventory/sale_list.html'
    context_object_name = 'sales'

    def get_queryset(self):
        qs = Sale.objects.select_related('product', 'customer').annotate(
            total_amount=ExpressionWrapper(                                     # fetch the data and annotate can calculate all orders
                F('quantity') * F('price'),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        ).order_by('-date', '-id')
        if self.request.accounts_user.role != 'admin':                      # order by date and id and showing only admin
            qs = qs.filter(customer=self.request.accounts_user)             # user can show only his orders
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)                    # user can shows only his own orderss not the all orders
        ctx['my_orders_only'] = self.request.accounts_user.role != 'admin'
        return ctx


class SaleCreateView(LoggedInAccountsMixin, CreateView):
    model = Sale
    form_class = SaleForm
    template_name = 'inventory/sale_form.html'
    success_url = reverse_lazy('inventory:sale_list')

    def get_initial(self):                          # get data (default data)
        initial = super().get_initial()
        pid = self.request.GET.get('product')           # get product id
        if pid and str(pid).isdigit():              
            initial['product'] = int(pid)               # if product.id in url, fill product field automaitcally
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)                
        ctx['is_buy_flow'] = bool(self.request.GET.get('product'))          # if product in url : True - buy
        return ctx

    def form_valid(self, form):
        sale = form.save(commit=False)
        sale.customer = self.request.accounts_user          
        with transaction.atomic():                  
            product = Product.objects.select_for_update().get(pk=sale.product_id)
            if product.quantity < sale.quantity:
                form.add_error('quantity', 'Not enough stock on hand for this sale.')
                return self.form_invalid(form)
            product.quantity -= sale.quantity
            product.save()
            sale.save()
        total = sale.quantity * sale.price
        messages.success(self.request, f'Order placed. Total amount: {total}')
        return redirect(self.success_url)


# from django.shortcuts import render, redirect, get_object_or_404
# from .models import Category
# from .forms import CategoryForm

# def category_list(request):
#     categories = Category.objects.all()
#     return render(request, 'inventory/category_list.html', {'categories': categories})


# def category_create(request):
#     if request.method == 'POST':
#         form = CategoryForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('inventory:category_list')
#     else:
#         form = CategoryForm()

#     return render(request, 'inventory/category_form.html', {'form': form})


# def category_update(request, id):
#     category = get_object_or_404(Category, id=id)

#     if request.method == 'POST':
#         form = CategoryForm(request.POST, instance=category)
#         if form.is_valid():
#             form.save()
#             return redirect('inventory:category_list')
#     else:
#         form = CategoryForm(instance=category)

#     return render(request, 'inventory/category_form.html', {'form': form})


# def category_delete(request, id):
#     category = get_object_or_404(Category, id=id)

#     if request.method == 'POST':
#         category.delete()
#         return redirect('inventory:category_list')

#     return render(request, 'inventory/category_confirm_delete.html', {'category': category})


# from .models import Product
# from .forms import ProductForm

# def product_list(request):
#     products = Product.objects.all()
#     return render(request, 'inventory/product_list.html', {'products': products})


# def product_create(request):
#     if request.method == 'POST':
#         form = ProductForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('inventory:product_list')
#     else:
#         form = ProductForm()

#     return render(request, 'inventory/product_form.html', {'form': form})


# def product_update(request, id):
#     product = get_object_or_404(Product, id=id)

#     if request.method == 'POST':
#         form = ProductForm(request.POST, instance=product)
#         if form.is_valid():
#             form.save()
#             return redirect('inventory:product_list')
#     else:
#         form = ProductForm(instance=product)

#     return render(request, 'inventory/product_form.html', {'form': form})


# def product_delete(request, id):
#     product = get_object_or_404(Product, id=id)

#     if request.method == 'POST':
#         product.delete()
#         return redirect('inventory:product_list')

#     return render(request, 'inventory/product_confirm_delete.html', {'product': product})


# from .models import Purchase

# def purchase_list(request):
#     purchases = Purchase.objects.all().order_by('-id')
#     return render(request, 'inventory/purchase_list.html', {'purchases': purchases})


# def purchase_create(request):
#     if request.method == 'POST':
#         form = PurchaseForm(request.POST)
#         if form.is_valid():
#             purchase = form.save(commit=False)

#             product = purchase.product
#             product.quantity += purchase.quantity
#             product.save()

#             purchase.save()
#             return redirect('inventory:purchase_list')
#     else:
#         form = PurchaseForm()

#     return render(request, 'inventory/purchase_form.html', {'form': form})



# from .models import Sale

# def sale_list(request):
#     sales = Sale.objects.all().order_by('-id')
#     return render(request, 'inventory/sale_list.html', {'sales': sales})


# def sale_create(request):
#     if request.method == 'POST':
#         form = SaleForm(request.POST)
#         if form.is_valid():
#             sale = form.save(commit=False)

#             product = sale.product

#             if product.quantity < sale.quantity:
#                 return render(request, 'inventory/sale_form.html', {
#                     'form': form,
#                     'error': 'Not enough stock'
#                 })

#             product.quantity -= sale.quantity
#             product.save()

#             sale.save()
#             return redirect('inventory:sale_list')
#     else:
#         form = SaleForm()

#     return render(request, 'inventory/sale_form.html', {'form': form})



# def dashboard(request):
#     products = Product.objects.all()
#     categories = Category.objects.all()

#     return render(request, 'inventory/dashboard.html', {
#         'product_count': products.count(),
#         'category_count': categories.count(),
#     })