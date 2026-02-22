import json
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm, AddToCartForm, ProfileEditForm
from pages.models import Category, CartItem, Order, Product, PromoCode, PromoCodeUsage, Wishlist, OrderItem
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum, F
from decimal import Decimal
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone


CATEGORY_META = {
    'fruits':    {'name': 'Fruits & Vegetables', 'icon': '🥦'},
    'dairy':     {'name': 'Dairy & Eggs',         'icon': '🥚'},
    'meat':      {'name': 'Meat & Poultry',        'icon': '🥩'},
    'seafood':   {'name': 'Seafood',               'icon': '🦐'},
    'bakery':    {'name': 'Bakery & Bread',         'icon': '🍞'},
    'canned':    {'name': 'Canned Goods',           'icon': '🥫'},
    'frozen':    {'name': 'Frozen Foods',           'icon': '❄️'},
    'pasta':     {'name': 'Pasta & Rice',           'icon': '🍝'},
    'breakfast': {'name': 'Breakfast Foods',        'icon': '🥞'},
    'snacks':    {'name': 'Snacks & Chips',         'icon': '🍿'},
    'beverages': {'name': 'Beverages',              'icon': '🥤'},
    'spices':    {'name': 'Spices & Seasonings',    'icon': '🌶️'},
    'baby':      {'name': 'Baby Food',              'icon': '🍼'},
    'health':    {'name': 'Health & Wellness',      'icon': '💊'},
    'household': {'name': 'Household Supplies',     'icon': '🧹'},
    'personal':  {'name': 'Personal Care',          'icon': '🧴'},
    'pet':       {'name': 'Pet Food & Supplies',    'icon': '🐾'},
}


def category_view(request, slug):
    meta = CATEGORY_META.get(slug, {
        'name': slug.replace('-', ' ').title(),
        'icon': '🛒',
    })

    category_obj = None
    category_name = meta['name']

    try:
        category_obj = Category.objects.get(slug=slug)
    except Category.DoesNotExist:
        pass

    if not category_obj:
        try:
            category_obj = Category.objects.filter(name__icontains=slug).first()
        except:
            pass

    if category_obj:
        products = Product.objects.filter(category=category_obj)
        category_name = category_obj.name
    else:
        products = Product.objects.none()

    search_query = request.GET.get('q', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    sort_by = request.GET.get('sort', '-created_at')
    allowed_sorts = ['price', '-price', 'name', '-name', 'created_at', '-created_at']
    if sort_by in allowed_sorts:
        products = products.order_by(sort_by)

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    try:
        products_page = paginator.page(page_number)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)

    context = {
        'slug': slug,
        'category_name': category_name,
        'category_icon': meta.get('icon', '🛒'),
        'category': category_obj,
        'products': products_page,
        'search_query': search_query,
        'current_sort': sort_by,
        'product_count': paginator.count,
        'signup_form': SignUpForm(),
        'signin_form': AuthenticationForm(),
    }
    return render(request, 'categories/category.html', context)


def home(request):
    categories = Category.objects.all()
    category_slug = request.GET.get('category', '')
    sort_by = request.GET.get('sort', '-created_at')
    search_query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)

    products = Product.objects.all()

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    allowed_sorts = ['price', '-price', 'name', '-name', 'created_at', '-created_at']
    if sort_by in allowed_sorts:
        products = products.order_by(sort_by)

    paginator = Paginator(products, 12)
    try:
        products_page = paginator.page(page_number)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)

    context = {
        'categories': categories,
        'products': products_page,
        'signup_form': SignUpForm(),
        'signin_form': AuthenticationForm(),
        'current_category': category_slug,
        'current_sort': sort_by,
        'search_query': search_query,
        'banner_1': 'images/banner-ad-1.jpg',
        'banner_2': 'images/banner-ad-2.jpg',
        'banner_3': 'images/banner-ad-3.jpg',
        'banner_newsletter': 'images/banner-newsletter.jpg',
    }
    return render(request, 'home.html', context)


@csrf_exempt
def apply_promo_code(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code', '').strip().upper()
            order_amount = float(data.get('order_amount', 0))
            delivery_cost = float(data.get('delivery_cost', 0))

            if not code:
                return JsonResponse({'success': False, 'message': 'Введите промокод'}, status=400)
            if order_amount <= 0:
                return JsonResponse({'success': False, 'message': 'Неверная сумма заказа'}, status=400)

            try:
                promo = PromoCode.objects.get(code=code)
            except PromoCode.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Промокод не найден'}, status=404)

            is_valid, message = promo.is_valid()
            if not is_valid:
                return JsonResponse({'success': False, 'message': message}, status=400)

            discount_amount, free_shipping, discount_message = promo.calculate_discount(order_amount, delivery_cost)

            if discount_amount == 0 and not free_shipping:
                return JsonResponse({'success': False, 'message': discount_message}, status=400)

            return JsonResponse({
                'success': True,
                'message': f'✅ Промокод применен! {discount_message}',
                'data': {
                    'code': promo.code,
                    'discount_type': promo.discount_type,
                    'discount_amount': float(discount_amount),
                    'original_amount': order_amount,
                    'delivery_cost': delivery_cost,
                    'free_shipping': free_shipping,
                    'final_amount': order_amount - discount_amount + (0 if free_shipping else delivery_cost),
                    'description': promo.get_discount_display()
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Неверный формат данных'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Ошибка: {str(e)}'}, status=500)

    return JsonResponse({'success': False, 'message': 'Метод не разрешен'}, status=405)


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Dobro pozhalovat, {user.username}!')
            return redirect('shop:home')
        else:
            return render(request, 'base.html', {
                'signup_form': form,
                'signin_form': AuthenticationForm()
            })
    return render(request, 'base.html', {
        'signup_form': SignUpForm(),
        'signin_form': AuthenticationForm()
    })


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Dobro pozhalovat, {user.username}!')
            return redirect('shop:home')
        else:
            return render(request, 'base.html', {
                'signin_form': form,
                'signup_form': SignUpForm()
            })
    return render(request, 'base.html', {
        'signin_form': AuthenticationForm(),
        'signup_form': SignUpForm()
    })


def logout_view(request):
    logout(request)
    messages.info(request, 'Vy uspeshno vyshli iz sistemy.')
    return redirect('shop:home')


@login_required(login_url='login')
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    subtotal = sum(item.get_subtotal() for item in cart_items)
    tax = subtotal * Decimal('0.13')
    total = subtotal + tax
    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax': tax,
        'total': total
    })


def cart(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        if product_id:
            product = get_object_or_404(Product, id=product_id)
            if request.user.is_authenticated:
                cart_item, created = CartItem.objects.get_or_create(
                    user=request.user, product=product, defaults={"quantity": 1}
                )
            else:
                if not request.session.session_key:
                    request.session.create()
                cart_item, created = CartItem.objects.get_or_create(
                    session_key=request.session.session_key,
                    product=product,
                    defaults={"quantity": 1}
                )
            if not created:
                cart_item.quantity += 1
                cart_item.save()
            return redirect("shop:cart")

        action = request.POST.get("action")
        item_id = request.POST.get("item_id")
        if action and item_id:
            cart_item = get_object_or_404(CartItem, id=item_id)
            if action == "increase":
                cart_item.quantity += 1
                cart_item.save()
            elif action == "decrease":
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    cart_item.save()
                else:
                    cart_item.delete()
            elif action == "remove":
                cart_item.delete()
            return redirect("shop:cart")

    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart_items = CartItem.objects.filter(session_key=request.session.session_key)

    cart_items = cart_items.select_related('product')
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    shipping = 0
    total = subtotal + shipping

    now = timezone.now()
    available_promos = PromoCode.objects.filter(
        is_active=True
    ).filter(
        Q(valid_from__lte=now) | Q(valid_from__isnull=True)
    ).filter(
        Q(valid_until__gte=now) | Q(valid_until__isnull=True)
    ).exclude(
        usage_limit__isnull=False,
        times_used__gte=F('usage_limit')
    ).order_by('-created_at')[:10]

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
        'item_count': sum(item.quantity for item in cart_items),
        'available_promos': available_promos,
    }
    return render(request, 'cart.html', context)


def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
    return redirect('cart')


def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        cart[str(product_id)] += 1
    else:
        cart[str(product_id)] = 1
    request.session['cart'] = cart
    return redirect('cart')


@login_required(login_url='login')
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    return redirect('cart')


@login_required(login_url='login')
def apply_discount(request):
    if request.method == "POST":
        code = request.POST.get("discount_code", "")
        request.session['discount_code'] = code
    return redirect('cart')


def edit_cart_item(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk)
    action = request.GET.get('action')
    if action == 'decrement' and cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    elif action == 'increment':
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart')


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
        cart_items.delete()
        return redirect('checkout_success')
    return render(request, 'checkout.html', {
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total
    })


@login_required
def checkout_success(request):
    return render(request, 'checkout_success.html')


@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        return redirect('cart')
    if request.method == 'POST':
        order = Order.objects.create(
            user=request.user,
            total=sum(item.get_subtotal() for item in cart_items),
            payment_method="Card"
        )
        cart_items.delete()
        return redirect('order_success', order_id=order.id)
    return render(request, 'checkout.html', {'cart_items': cart_items})


def zakaz_view(request):
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart_items = CartItem.objects.filter(session_key=session_key)

    if request.method == 'POST':
        delivery_city = request.POST.get('delivery_city', '')
        delivery_distance = request.POST.get('delivery_distance', 0)
        delivery_cost = request.POST.get('delivery_cost', 0)
        promo_code = request.POST.get('promo_code', '').strip().upper()
        discount_amount = request.POST.get('discount_amount', 0)

        try:
            delivery_distance = int(delivery_distance)
            delivery_cost = int(delivery_cost)
            discount_amount = float(discount_amount)
        except (ValueError, TypeError):
            delivery_distance = 0
            delivery_cost = 0
            discount_amount = 0

        total_amount = sum(item.get_subtotal() for item in cart_items)

        promo_obj = None
        if promo_code:
            try:
                promo_obj = PromoCode.objects.get(code=promo_code)
            except PromoCode.DoesNotExist:
                pass

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            total_amount=total_amount,
            delivery_city=delivery_city,
            delivery_distance=delivery_distance,
            delivery_cost=delivery_cost,
            discount_amount=discount_amount,
            promo_code=promo_obj,
            status='processing'
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        if promo_obj:
            promo_obj.use()
            PromoCodeUsage.objects.create(
                promo_code=promo_obj,
                order=order,
                order_amount=total_amount,
                discount_amount=discount_amount,
                user=request.user if request.user.is_authenticated else None
            )

        cart_items.delete()
        messages.success(request, 'Vash zakaz uspeshno oformlen!')
        return redirect('shop:moizakazu')

    subtotal = sum(item.get_subtotal() for item in cart_items)
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': 0,
        'total': subtotal,
    }
    return render(request, 'zakaz.html', context)


@login_required
def create_order(request):
    if request.method == 'POST':
        cart_items = request.POST.get('cart_items')
        Order.objects.create(user=request.user, items=cart_items)
        return redirect('shop:moizakazu')
    return redirect('shop:cart')


@login_required
def moizakazu(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
    return render(request, 'moizakazu.html', {'orders': orders})


@login_required
def product_orders_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    orders = Order.objects.filter(cartitem__product=product, user=request.user).distinct()
    return render(request, 'product_orders.html', {'product': product, 'orders': orders})


def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, 'product_detail.html', {'product': product})


# ─────────────────────────────────────────────
#  CREATE TOVAR — ИСПРАВЛЕННЫЙ
# ─────────────────────────────────────────────
@login_required(login_url='shop:login')
def create_tovar(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price', '0')
        category_id = request.POST.get('category')
        unit_type = request.POST.get('unit_type', 'pcs')
        image = request.FILES.get('image')

        if not name or not price:
            messages.error(request, 'Заполните все обязательные поля!')
            return render(request, 'create_tovar.html', {'categories': categories})

        try:
            price = Decimal(price)
        except:
            messages.error(request, 'Неверный формат цены!')
            return render(request, 'create_tovar.html', {'categories': categories})

        category = None
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                pass

        Product.objects.create(
            name=name,
            description=description,
            price=price,
            category=category,
            unit_type=unit_type,
            image=image,
        )

        messages.success(request, f'Товар "{name}" успешно создан!')
        return redirect('shop:home')

    return render(request, 'create_tovar.html', {'categories': categories})


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


@login_required(login_url='shop:login')
def wishlist(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id)
        wishlist_item = Wishlist.objects.filter(user=request.user, product=product)
        if wishlist_item.exists():
            wishlist_item.delete()
        else:
            Wishlist.objects.create(user=request.user, product=product)
        return redirect(request.META.get('HTTP_REFERER', 'shop:home'))
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})


@require_POST
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    return redirect("wishlist")


def profile(request):
    return render(request, 'base.html', {
        'signup_form': SignUpForm(),
        'signin_form': AuthenticationForm()
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


def balance_view(request):
    return render(request, 'balance.html')


def courier_page(request):
    return render(request, 'courier.html')




from .models import UserSettings


@login_required
def settings_view(request):
    """Страница с панелью настроек."""
    # Получаем или создаём настройки текущего пользователя
    user_settings, _ = UserSettings.objects.get_or_create(user=request.user)
    return render(request, 'settings.html', {
        'user': request.user,
        'settings': user_settings,
    })

@login_required
@require_POST
def settings_save(request):
    """
    Универсальный endpoint для сохранения настроек.
    Принимает JSON, обрабатывает:
      - username
      - email
      - old_password + new_password
      - dark_mode, analytics, twofa (bool)
      - language (str)
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    user = request.user

    # ── Изменить имя пользователя ──
    if 'username' in data:
        new_username = data['username'].strip()
        if not new_username:
            return JsonResponse({'success': False, 'error': 'Имя не может быть пустым'})
        from django.contrib.auth.models import User
        if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
            return JsonResponse({'success': False, 'error': 'Это имя уже занято'})
        user.username = new_username
        user.save(update_fields=['username'])
        return JsonResponse({'success': True})

    # ── Изменить email ──
    if 'email' in data:
        new_email = data['email'].strip()
        if not new_email or '@' not in new_email:
            return JsonResponse({'success': False, 'error': 'Некорректный email'})
        user.email = new_email
        user.save(update_fields=['email'])
        return JsonResponse({'success': True})

    # ── Сменить пароль ──
    if 'old_password' in data and 'new_password' in data:
        if not user.check_password(data['old_password']):
            return JsonResponse({'success': False, 'error': 'Неверный текущий пароль'})
        new_pw = data['new_password']
        if len(new_pw) < 6:
            return JsonResponse({'success': False, 'error': 'Минимум 6 символов'})
        user.set_password(new_pw)
        user.save()
        # обновляем сессию чтобы не разлогинился
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)
        return JsonResponse({'success': True})

    # ── Сохранить настройки (тогглы, язык) ──
    user_settings, _ = UserSettings.objects.get_or_create(user=user)

    if 'dark_mode' in data:
        user_settings.dark_mode = bool(data['dark_mode'])
    if 'analytics' in data:
        user_settings.analytics = bool(data['analytics'])
    if 'twofa' in data:
        user_settings.twofa = bool(data['twofa'])
    if 'language' in data:
        user_settings.language = data['language']

    user_settings.save()
    return JsonResponse({'success': True})





@login_required
def change_name(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        request.user.first_name = data.get('first_name', '').strip()
        request.user.last_name  = data.get('last_name', '').strip()
        request.user.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def change_email(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        request.user.email = data.get('email', '').strip()
        request.user.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def change_username(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        from django.contrib.auth.models import User
        new_username = data.get('username', '').strip()
        if User.objects.filter(username=new_username).exclude(pk=request.user.pk).exists():
            return JsonResponse({'success': False, 'error': 'Логин уже занят'})
        request.user.username = new_username
        request.user.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def change_password(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        user = request.user
        if not user.check_password(data.get('old_password', '')):
            return JsonResponse({'success': False, 'error': 'Неверный старый пароль'})
        if data.get('new_password1') != data.get('new_password2'):
            return JsonResponse({'success': False, 'error': 'Пароли не совпадают'})
        if len(data.get('new_password1', '')) < 6:
            return JsonResponse({'success': False, 'error': 'Минимум 6 символов'})
        user.set_password(data['new_password1'])
        user.save()
        update_session_auth_hash(request, user)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def change_phone(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        profile = request.user.profile
        profile.phone = data.get('phone', '').strip()
        profile.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)