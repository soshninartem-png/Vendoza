from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm, AddToCartForm, ProfileEditForm
from pages.models import Category, CartItem, Order, Product
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from decimal import Decimal

def home(request):
    categories = Category.objects.all()
    return render(request, 'home.html', {  
        'categories': categories,
        'signup_form': SignUpForm(),
        'signin_form': AuthenticationForm()
    })

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'base.html', {'signup_form': form, 'signin_form': AuthenticationForm()})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'base.html', {'signin_form': form, 'signup_form': SignUpForm()})

@login_required(login_url='login')
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    subtotal = sum(item.subtotal() for item in cart_items)

    tax = subtotal * Decimal('0.13')  # <--- Исправлено
    total = subtotal + tax

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax': tax,
        'total': total
    })

@login_required
def checkout_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        return redirect('cart')
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    shipping = 5.99
    total = subtotal + shipping
    if request.method == "POST":
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        Order.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            address=address,
            total_price=total
        )
        cart_items.delete()  # очистка корзины
        return redirect('checkout_success')
    return render(request, 'checkout.html', {
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total
    })

@login_required
def checkout_success(request):
    return render(request, 'checkout_success.html')

def search_view(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category')
    products = Product.objects.all()
    categories = Category.objects.all()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category_id and category_id != 'all':
        products = products.filter(category_id=category_id)
    return render(request, 'search_results.html', {
        'products': products,
        'query': query,
        'categories': categories,
        'selected_category': category_id
    })

def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
    return redirect('cart')

def logout_view(request):
    logout(request)
    return redirect('home')

def profile(request):
    return render(request, 'base.html', {'signup_form': SignUpForm(), 'signin_form': AuthenticationForm()})

@login_required
def product_orders_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    orders = Order.objects.filter(cartitem__product=product, user=request.user).distinct()
    return render(request, 'product_orders.html', {'product': product, 'orders': orders})






@login_required(login_url='login')
def add_to_cart(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        quantity = int(request.POST.get("quantity", 1))
        product = get_object_or_404(Product, id=product_id)

        # Используем модель CartItem
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

    # После добавления редирект на страницу корзины
    return redirect('cart')

@login_required(login_url='login')
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    subtotal = sum(item.subtotal() for item in cart_items)
    tax = subtotal * Decimal('0.13')  # Decimal, не float
    total = subtotal + tax

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax': tax,
        'total': total
    })


def cart(request):
    cart = request.session.get('cart', {})
    items = []
    total_price = 0

    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        item_total = product.price * quantity
        total_price += item_total

        items.append({
            'product': product,
            'quantity': quantity,
            'item_total': item_total
        })

    return render(request, 'cart.html', {
        'items': items,
        'total_price': total_price
    })



@login_required
def profile_edit(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('/')
    else:
        form = ProfileEditForm(instance=profile)

    return render(request, 'profile_edit.html', {'form': form})


@login_required(login_url='login')
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    return redirect('cart')



@login_required(login_url='login')
def apply_discount(request):
    if request.method == "POST":
        code = request.POST.get("discount_code", "")
        # Здесь можно добавить логику проверки кода и пересчёта total
        # Например, сохранить в сессии или в модели Cart
        request.session['discount_code'] = code  # простой вариант
    return redirect('cart')