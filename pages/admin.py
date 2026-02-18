from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Sum, Count
from .models import (
    Category, Product, CartItem, Order, OrderItem, 
    Profile, Wishlist, PromoCode, PromoCodeUsage
)


# ============================================
# КАТЕГОРИИ
# ============================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'image_preview', 'slug', 'product_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.image.url
            )
        return mark_safe('<div style="width: 60px; height: 60px; background: #f0f0f0; border-radius: 8px; display: flex; align-items: center; justify-content: center;">📁</div>')
    image_preview.short_description = '🖼️ Фото'
    
    def product_count(self, obj):
        count = obj.product_set.count()
        return format_html(
            '<span style="background: #e3f2fd; color: #1976d2; padding: 4px 12px; border-radius: 12px; font-weight: 600;">{} товаров</span>',
            count
        )
    product_count.short_description = '📦 Товаров'


# ============================================
# ПРОДУКТЫ
# ============================================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('image_preview', 'name', 'price_display', 'category', 'unit_type', 'created_display')
    list_filter = ('category', 'unit_type', 'created_at')
    search_fields = ('name', 'description')
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('📝 Основная информация', {
            'fields': ('name', 'description', 'category')
        }),
        ('💰 Цена и единицы', {
            'fields': ('price', 'unit_type')
        }),
        ('🖼️ Изображение', {
            'fields': ('image',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />',
                obj.image.url
            )
        return mark_safe('<div style="width: 80px; height: 80px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; font-size: 32px;">📦</div>')
    image_preview.short_description = '🖼️'
    
    def price_display(self, obj):
        return format_html(
            '<span style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 14px;">${}</span>',
            obj.price
        )
    price_display.short_description = '💵 Цена'
    
    def created_display(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    created_display.short_description = '📅 Создан'


# ============================================
# ПРОМОКОДЫ
# ============================================
@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = [
        'code_badge',
        'discount_preview', 
        'status_indicator',
        'usage_progress',
        'validity_badge',
        'created_display'
    ]
    
    list_filter = [
        'discount_type', 
        'is_active', 
        ('created_at', admin.DateFieldListFilter),
        ('valid_until', admin.DateFieldListFilter),
    ]
    
    search_fields = ['code', 'description']
    readonly_fields = ['times_used', 'created_at', 'updated_at', 'promo_preview']
    
    fieldsets = (
        ('🎫 ПРОМОКОД', {
            'fields': ('code', 'description', 'is_active'),
            'description': '''
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                    <h2 style="margin: 0 0 10px 0; font-size: 24px;">✨ Создание промокода</h2>
                    <p style="margin: 0; opacity: 0.9;">Создайте уникальный промокод для ваших клиентов</p>
                </div>
            '''
        }),
        ('🎯 ТИП СКИДКИ', {
            'fields': ('discount_type',),
        }),
        ('💰 ПАРАМЕТРЫ СКИДКИ', {
            'fields': ('discount_percentage', 'max_discount_amount', 'discount_amount'),
        }),
        ('⚙️ УСЛОВИЯ', {
            'fields': ('minimum_order_amount',),
        }),
        ('🔢 ОГРАНИЧЕНИЯ', {
            'fields': ('usage_limit', 'valid_from', 'valid_until'),
        }),
        ('📊 СТАТИСТИКА', {
            'fields': ('times_used', 'promo_preview', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        })
    )
    
    actions = ['activate_codes', 'deactivate_codes', 'duplicate_codes']
    
    def code_badge(self, obj):
        return format_html(
            '<div style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 8px 20px; border-radius: 25px; font-weight: 700; font-size: 16px; letter-spacing: 1px; box-shadow: 0 4px 15px rgba(102,126,234,0.4);">{}</div>',
            obj.code
        )
    code_badge.short_description = '🎫 КОД'
    
    def discount_preview(self, obj):
        if obj.discount_type == 'percentage':
            color = '#28a745'
            icon = '📊'
            text = f"{obj.discount_percentage}%"
        elif obj.discount_type == 'fixed':
            color = '#007bff'
            icon = '💵'
            text = f"${obj.discount_amount}"
        else:
            color = '#ffc107'
            icon = '🚚'
            text = "FREE"
        
        return format_html(
            '<div style="display: inline-flex; align-items: center; gap: 8px; background: {}; color: white; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 14px;"><span style="font-size: 18px;">{}</span>{}</div>',
            color, icon, text
        )
    discount_preview.short_description = '💰 СКИДКА'
    
    def status_indicator(self, obj):
        # ✅ ИСПРАВЛЕНО: был format_html без аргументов — Django 6.0 не принимает
        is_valid, message = obj.is_valid()
        if is_valid:
            return format_html(
                '<div style="display: inline-flex; align-items: center; gap: 6px; background: #d4edda; color: #155724; padding: 6px 14px; border-radius: 20px; font-weight: 600; border: 2px solid #28a745;"><span style="font-size: 16px;">✅</span>{}</div>',
                'Активен'
            )
        else:
            return format_html(
                '<div style="display: inline-flex; align-items: center; gap: 6px; background: #f8d7da; color: #721c24; padding: 6px 14px; border-radius: 20px; font-weight: 600; border: 2px solid #dc3545;"><span style="font-size: 16px;">❌</span>{}</div>',
                message[:15]
            )
    status_indicator.short_description = '📊 СТАТУС'
    
    def usage_progress(self, obj):
        if obj.usage_limit:
            percentage = (obj.times_used / obj.usage_limit) * 100
            
            if percentage >= 100:
                bar_color = '#dc3545'
                text_color = '#721c24'
            elif percentage >= 75:
                bar_color = '#ffc107'
                text_color = '#856404'
            else:
                bar_color = '#28a745'
                text_color = '#155724'
            
            return format_html(
                '''<div style="width: 150px;">
                    <div style="background: #e9ecef; border-radius: 10px; height: 24px; overflow: hidden; position: relative;">
                        <div style="background: {}; width: {}%; height: 100%;"></div>
                        <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; color: {}; font-weight: 700; font-size: 12px;">
                            {} / {}
                        </div>
                    </div>
                </div>''',
                bar_color, min(percentage, 100), text_color, obj.times_used, obj.usage_limit
            )
        else:
            return mark_safe(
                '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 6px 16px; border-radius: 20px; font-weight: 700; text-align: center;">∞ Безлимит</div>'
            )
    usage_progress.short_description = '📈 ИСПОЛЬЗОВАНО'
    
    def validity_badge(self, obj):
        from django.utils import timezone
        now = timezone.now()
        
        if obj.valid_until:
            days_left = (obj.valid_until - now).days
            
            if days_left < 0:
                return mark_safe('<div style="background: #f8d7da; color: #721c24; padding: 6px 12px; border-radius: 20px; font-weight: 600; font-size: 12px;">⏰ Истек</div>')
            elif days_left == 0:
                return mark_safe('<div style="background: #fff3cd; color: #856404; padding: 6px 12px; border-radius: 20px; font-weight: 600; font-size: 12px;">⚠️ Сегодня</div>')
            elif days_left <= 7:
                return format_html(
                    '<div style="background: #fff3cd; color: #856404; padding: 6px 12px; border-radius: 20px; font-weight: 600; font-size: 12px;">⏰ {} дн.</div>',
                    days_left
                )
            else:
                return format_html(
                    '<div style="background: #d4edda; color: #155724; padding: 6px 12px; border-radius: 20px; font-weight: 600; font-size: 12px;">✅ {} дн.</div>',
                    days_left
                )
        else:
            return mark_safe(
                '<div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 6px 12px; border-radius: 20px; font-weight: 700; font-size: 12px;">♾️ Бессрочно</div>'
            )
    validity_badge.short_description = '⏰ СРОК'
    
    def created_display(self, obj):
        return obj.created_at.strftime('%d.%m.%Y')
    created_display.short_description = '📅 Создан'
    
    def promo_preview(self, obj):
        # ✅ ИСПРАВЛЕНО: строим HTML через format_html с аргументами, не через .format() + format_html()
        if obj.discount_type == 'percentage':
            discount_text = f"{obj.discount_percentage}%"
        elif obj.discount_type == 'fixed':
            discount_text = f"${obj.discount_amount}"
        else:
            discount_text = "Бесплатная доставка"

        extra = ''
        if obj.minimum_order_amount and obj.minimum_order_amount > 0:
            extra = f'<div style="margin-top:15px;padding-top:15px;border-top:1px solid rgba(255,255,255,0.3);"><div style="opacity:0.8;font-size:12px;margin-bottom:5px;">МИНИМУМ</div><div style="font-weight:700;font-size:16px;">${obj.minimum_order_amount}</div></div>'

        return format_html(
            '''<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 16px; box-shadow: 0 10px 40px rgba(102,126,234,0.3); max-width: 400px;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="font-size: 48px; margin-bottom: 10px;">🎫</div>
                    <div style="font-size: 32px; font-weight: 800; letter-spacing: 2px;">{}</div>
                    <div style="font-size: 14px; opacity: 0.9; margin-top: 10px;">{}</div>
                </div>
                <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 12px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div>
                            <div style="opacity: 0.8; font-size: 12px; margin-bottom: 5px;">ТИП СКИДКИ</div>
                            <div style="font-weight: 700; font-size: 16px;">{}</div>
                        </div>
                        <div>
                            <div style="opacity: 0.8; font-size: 12px; margin-bottom: 5px;">СКИДКА</div>
                            <div style="font-weight: 700; font-size: 16px;">{}</div>
                        </div>
                    </div>
                    {}
                </div>
            </div>''',
            obj.code,
            obj.description or 'Промокод',
            obj.get_discount_type_display(),
            discount_text,
            mark_safe(extra)
        )
    promo_preview.short_description = '👁️ Предпросмотр'
    
    def activate_codes(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✅ Активировано {updated} промокодов', level='success')
    activate_codes.short_description = '✅ Активировать'
    
    def deactivate_codes(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'❌ Деактивировано {updated} промокодов', level='warning')
    deactivate_codes.short_description = '❌ Деактивировать'
    
    def duplicate_codes(self, request, queryset):
        count = queryset.count()
        for promo in queryset:
            promo.pk = None
            promo.code = f"{promo.code}_COPY"
            promo.times_used = 0
            promo.save()
        self.message_user(request, f'📋 Создано {count} копий', level='success')
    duplicate_codes.short_description = '📋 Дублировать'


# ============================================
# ИСТОРИЯ ИСПОЛЬЗОВАНИЯ ПРОМОКОДОВ
# ============================================
@admin.register(PromoCodeUsage)
class PromoCodeUsageAdmin(admin.ModelAdmin):
    list_display = [
        'promo_badge',
        'order_link',
        'user_info',
        'amounts_display',
        'date_display'
    ]
    
    list_filter = ['used_at', 'promo_code']
    search_fields = ['promo_code__code', 'user__username']
    readonly_fields = ['promo_code', 'order', 'order_amount', 'discount_amount', 'user', 'used_at']
    date_hierarchy = 'used_at'
    
    def promo_badge(self, obj):
        return format_html(
            '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 6px 14px; border-radius: 20px; font-weight: 700; display: inline-block;">{}</div>',
            obj.promo_code.code
        )
    promo_badge.short_description = '🎫 Промокод'
    
    def order_link(self, obj):
        if obj.order:
            url = reverse('admin:pages_order_change', args=[obj.order.id])
            return format_html(
                '<a href="{}" style="color: #007bff; font-weight: 600; text-decoration: none;">📦 Заказ #{}</a>',
                url, obj.order.order_number
            )
        return '-'
    order_link.short_description = '📦 Заказ'
    
    def user_info(self, obj):
        if obj.user:
            return format_html(
                '<div style="display: flex; align-items: center; gap: 8px;"><span style="font-size: 20px;">👤</span><strong>{}</strong></div>',
                obj.user.username
            )
        return '-'
    user_info.short_description = '👤 Пользователь'
    
    def amounts_display(self, obj):
        return format_html(
            '''<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                <div style="background: #e3f2fd; padding: 8px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 11px; color: #1976d2; margin-bottom: 4px;">ЗАКАЗ</div>
                    <div style="font-weight: 700; color: #1976d2;">${}</div>
                </div>
                <div style="background: #d4edda; padding: 8px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 11px; color: #28a745; margin-bottom: 4px;">СКИДКА</div>
                    <div style="font-weight: 700; color: #28a745;">-${}</div>
                </div>
            </div>''',
            obj.order_amount, obj.discount_amount
        )
    amounts_display.short_description = '💰 Суммы'
    
    def date_display(self, obj):
        return obj.used_at.strftime('%d.%m.%Y %H:%M')
    date_display.short_description = '📅 Дата'
    
    def has_add_permission(self, request):
        return False


# ============================================
# ЗАКАЗЫ
# ============================================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_badge',
        'user_info',
        'status_badge',
        'financial_summary',
        'promo_info',
        'created_display'
    ]
    
    list_filter = ['status', 'created_at', 'promo_code']
    search_fields = ['order_number', 'user__username', 'delivery_city']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('📦 Информация о заказе', {
            'fields': ('order_number', 'user', 'status')
        }),
        ('💰 Финансы', {
            'fields': ('total_amount', 'delivery_cost', 'discount_amount', 'promo_code')
        }),
        ('🚚 Доставка', {
            'fields': ('delivery_city', 'delivery_distance', 'pickup_point', 'storage_deadline')
        }),
        ('📝 Дополнительно', {
            'fields': ('notes', 'created_at', 'updated_at')
        })
    )
    
    def order_badge(self, obj):
        return format_html(
            '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 8px 16px; border-radius: 20px; font-weight: 700; display: inline-block;">#{}</div>',
            obj.order_number
        )
    order_badge.short_description = '📦 Номер'
    
    def user_info(self, obj):
        if obj.user:
            return format_html(
                '<div><strong>{}</strong><br><span style="color: #666; font-size: 12px;">{}</span></div>',
                obj.user.username,
                obj.user.email
            )
        return 'Гость'
    user_info.short_description = '👤 Клиент'
    
    def status_badge(self, obj):
        colors = {
            'pending':    ('#fff3cd', '#856404', '⏳'),
            'processing': ('#cfe2ff', '#084298', '📦'),
            'shipping':   ('#cfe2ff', '#084298', '🚚'),
            'delivered':  ('#d4edda', '#155724', '✅'),
            'picked-up':  ('#e7d4f5', '#6f42c1', '🎉'),
            'cancelled':  ('#f8d7da', '#721c24', '❌'),
        }
        bg, text, icon = colors.get(obj.status, ('#e2e3e5', '#383d41', '❓'))
        return format_html(
            '<div style="background: {}; color: {}; padding: 6px 14px; border-radius: 20px; font-weight: 700; display: inline-flex; align-items: center; gap: 6px;"><span style="font-size: 16px;">{}</span>{}</div>',
            bg, text, icon, obj.get_status_display()
        )
    status_badge.short_description = '📊 Статус'
    
    def financial_summary(self, obj):
        final = obj.get_final_total()
        return format_html(
            '''<div style="background: #f8f9fa; padding: 12px; border-radius: 8px;">
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; font-size: 12px;">
                    <div>Товары: <strong>${}</strong></div>
                    <div>Доставка: <strong>${}</strong></div>
                    <div style="color: #28a745;">Скидка: <strong>-${}</strong></div>
                    <div style="grid-column: span 2; margin-top: 8px; padding-top: 8px; border-top: 2px solid #dee2e6; font-size: 14px; color: #667eea; font-weight: 700;">ИТОГО: ${}</div>
                </div>
            </div>''',
            obj.total_amount, obj.delivery_cost, obj.discount_amount, final
        )
    financial_summary.short_description = '💵 Финансы'
    
    def promo_info(self, obj):
        if obj.promo_code:
            return format_html(
                '<div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 6px 12px; border-radius: 20px; font-weight: 700; display: inline-block;">🎫 {}</div>',
                obj.promo_code.code
            )
        return '-'
    promo_info.short_description = '🎫 Промокод'
    
    def created_display(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    created_display.short_description = '📅 Создан'


# ============================================
# ОСТАЛЬНЫЕ МОДЕЛИ
# ============================================
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'subtotal_display']
    list_filter = ['order__created_at']
    search_fields = ['product__name', 'order__order_number']
    
    def subtotal_display(self, obj):
        return format_html(
            '<strong style="color: #28a745;">${}</strong>',
            obj.get_subtotal()
        )
    subtotal_display.short_description = '💰 Сумма'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity', 'subtotal_display', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__username', 'product__name']
    
    def subtotal_display(self, obj):
        return format_html(
            '<strong style="color: #007bff;">${}</strong>',
            obj.get_subtotal()
        )
    subtotal_display.short_description = '💰 Сумма'


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__username', 'product__name']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'nickname', 'rating_display']
    search_fields = ['user__username', 'nickname']
    
    def rating_display(self, obj):
        stars = '⭐' * int(obj.rating)
        return format_html(
            '<div style="font-size: 16px;">{} <span style="color: #666; font-size: 12px;">({}/5)</span></div>',
            stars, obj.rating
        )
    rating_display.short_description = '⭐ Рейтинг'