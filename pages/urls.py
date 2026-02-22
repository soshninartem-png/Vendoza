from django.urls import path
from . import views
from .views import balance_view

app_name = "shop"

urlpatterns = [
    path('', views.home, name='home'),
    path('courier/', views.courier_page, name='courier_page'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('zakaz/', views.zakaz_view, name='zakaz'),
    path('checkout/', views.checkout, name='checkout'),
    path('balance/', balance_view, name='balance'),
    path('checkout/success/', views.checkout_success, name='checkout_success'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('search/', views.search_view, name='search'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('create_tovar/', views.create_tovar, name='create_tovar'),
    path('moizakazu/', views.moizakazu, name='moizakazu'),
    path('api/apply-promo-code/', views.apply_promo_code, name='apply_promo_code'),
    path('settings/',       views.settings_view, name='settings'),
    path('settings/save/',  views.settings_save, name='settings-save'),
    # ✅ ОДИН маршрут вместо 17

    path('category/<slug:slug>/', views.category_view, name='category'),

    path('settings/change-phone/', views.change_phone, name='change_phone'),
    path('settings/change-name/',     views.change_name,     name='change_name'),
    path('settings/change-email/',    views.change_email,    name='change_email'),
    path('settings/change-username/', views.change_username, name='change_username'),
    path('settings/change-password/', views.change_password, name='change_password'),
]
