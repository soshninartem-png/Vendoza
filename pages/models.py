from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import random
import string


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    slug = models.SlugField(unique=True, blank=True, verbose_name='Слаг')
    image = models.ImageField(upload_to='category_images/', blank=True, null=True, verbose_name='Изображение')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']


class Product(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('pcs', 'Pieces'),
    ]

    name = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, default='No description', verbose_name='Описание')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Категория')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Изображение')
    unit_type = models.CharField(max_length=10, choices=UNIT_CHOICES, default='pcs', verbose_name='Единица измерения')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ['-created_at']


class CartItem(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart_items',
        null=True,
        blank=True,
        verbose_name='Пользователь'
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, verbose_name='Ключ сессии')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Продукт')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    added_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Элемент корзины'
        verbose_name_plural = 'Элементы корзины'
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    def get_subtotal(self):
        return self.product.price * self.quantity


class PromoCode(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Процент от суммы'),
        ('fixed', 'Фиксированная сумма'),
        ('free_shipping', 'Бесплатная доставка'),
    ]

    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Промокод',
        help_text='Уникальный код промокода (например: SALE50, FREESHIP)'
    )

    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        verbose_name='Тип скидки'
    )

    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Процент скидки',
        help_text='Для процентной скидки (0-100)'
    )

    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Сумма скидки ($)',
        help_text='Для фиксированной скидки'
    )

    minimum_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Минимальная сумма заказа ($)',
        help_text='Минимум товаров для применения'
    )

    max_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Максимальная сумма скидки ($)',
        help_text='Ограничение для процентной скидки'
    )

    usage_limit = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name='Лимит использований',
        help_text='Оставьте пустым для безлимитного'
    )

    times_used = models.IntegerField(
        default=0,
        verbose_name='Использовано раз',
        editable=False
    )

    valid_from = models.DateTimeField(
        default=timezone.now,
        verbose_name='Действителен с'
    )

    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Действителен до',
        help_text='Оставьте пустым для бессрочного'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Описание',
        help_text='Текст для клиента'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.get_discount_display()}"

    def get_discount_display(self):
        if self.discount_type == 'percentage':
            return f"{self.discount_percentage}% скидка"
        elif self.discount_type == 'fixed':
            return f"${self.discount_amount} скидка"
        elif self.discount_type == 'free_shipping':
            return "Бесплатная доставка"
        return "Неизвестная скидка"

    def is_valid(self):
        now = timezone.now()

        if not self.is_active:
            return False, "Промокод неактивен"

        if self.valid_from and now < self.valid_from:
            return False, "Промокод еще не активен"

        if self.valid_until and now > self.valid_until:
            return False, "Промокод истек"

        if self.usage_limit and self.times_used >= self.usage_limit:
            return False, "Промокод уже использован максимальное количество раз"

        return True, "Промокод действителен"

    def calculate_discount(self, order_amount, delivery_cost=0):
        """
        Вычисляет скидку на основе типа промокода.
        Возвращает: (discount_amount, free_shipping, message)
        """
        # Приводим всё к Decimal, чтобы не было конфликта типов
        order_amount = Decimal(str(order_amount))
        delivery_cost = Decimal(str(delivery_cost))

        if order_amount < self.minimum_order_amount:
            return Decimal('0'), False, f"Минимальная сумма заказа: ${self.minimum_order_amount}"

        discount_amount = Decimal('0')
        free_shipping = False

        if self.discount_type == 'percentage':
            # ПРОЦЕНТНАЯ СКИДКА
            discount_amount = (order_amount * self.discount_percentage) / Decimal('100')

            # Применяем максимальное ограничение
            if self.max_discount_amount and discount_amount > self.max_discount_amount:
                discount_amount = self.max_discount_amount

            message = f"Скидка {self.discount_percentage}%"
            if self.max_discount_amount:
                message += f" (макс. ${self.max_discount_amount})"

        elif self.discount_type == 'fixed':
            # ФИКСИРОВАННАЯ СКИДКА
            discount_amount = min(self.discount_amount, order_amount)
            message = f"Скидка ${self.discount_amount}"

        elif self.discount_type == 'free_shipping':
            # БЕСПЛАТНАЯ ДОСТАВКА
            free_shipping = True
            discount_amount = Decimal('0')
            message = "Бесплатная доставка"

        else:
            message = "Неверный тип скидки"

        return discount_amount, free_shipping, message

    def use(self):
        """Увеличить счетчик использований"""
        self.times_used += 1
        self.save(update_fields=['times_used'])

    @staticmethod
    def generate_random_code(length=8):
        characters = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choice(characters) for _ in range(length))
            if not PromoCode.objects.filter(code=code).exists():
                return code


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'В ожидании'),
        ('processing', 'Собирается'),
        ('shipping', 'Доставляется'),
        ('delivered', 'Доставлен'),
        ('picked-up', 'Выдан покупателю'),
        ('cancelled', 'Отменён'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Пользователь'
    )
    order_number = models.CharField(max_length=50, blank=True, verbose_name='Номер заказа', unique=True)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма товаров')
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Стоимость доставки')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Сумма скидки')

    promo_code = models.ForeignKey(
        'PromoCode',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Промокод'
    )

    delivery_city = models.CharField(max_length=100, null=True, blank=True, verbose_name='Город доставки')
    delivery_distance = models.IntegerField(default=0, verbose_name='Расстояние (км)')
    pickup_point = models.CharField(max_length=200, blank=True, default="Not specified", verbose_name='Пункт выдачи')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Последнее обновление')
    storage_deadline = models.DateTimeField(blank=True, null=True, verbose_name='Срок хранения')

    notes = models.TextField(blank=True, verbose_name='Примечания')

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD-{timezone.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

        if self.status == 'delivered' and not self.storage_deadline:
            self.storage_deadline = timezone.now() + timedelta(days=7)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Заказ #{self.order_number} - {self.user.username if self.user else 'Гость'}"

    def get_final_total(self):
        """Итоговая сумма = товары + доставка - скидка"""
        return self.total_amount + self.delivery_cost - self.discount_amount

    def get_items_count(self):
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Заказ')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Продукт')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена на момент заказа')

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    def get_subtotal(self):
        return self.price * self.quantity


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    nickname = models.CharField(max_length=30, verbose_name='Никнейм')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Аватар')
    bio = models.TextField(blank=True, verbose_name='О себе')
    rating = models.FloatField(default=5.0, verbose_name='Рейтинг')

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return self.nickname


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist', verbose_name='Пользователь')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist_items', verbose_name='Продукт')
    added_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class PromoCodeUsage(models.Model):
    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.CASCADE,
        related_name='usage_history',
        verbose_name='Промокод'
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Заказ'
    )

    order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма заказа ($)'
    )

    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма скидки ($)'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Пользователь'
    )

    used_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата использования'
    )

    class Meta:
        verbose_name = 'Использование промокода'
        verbose_name_plural = 'История использования промокодов'
        ordering = ['-used_at']

    def __str__(self):
        return f"{self.promo_code.code} - Заказ #{self.order.order_number if self.order else 'N/A'}"