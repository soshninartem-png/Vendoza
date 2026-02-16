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
    path('logout/', views.logout_view, name='logout'),

   
    path('fruits/', views.fruits, name='fruits'),
    path('dairy/', views.dairy, name='dairy'),
    path('meat/', views.meat, name='meat'),
    path('seafood/', views.seafood, name='seafood'),
    path('bakery/', views.bakery, name='bakery'),
    path('canned/', views.canned, name='canned'),
    path('frozen/', views.frozen, name='frozen'),
    path('pasta/', views.pasta, name='pasta'),
    path('breakfast/', views.breakfast, name='breakfast'),
    path('snacks/', views.snacks, name='snacks'),
    path('beverages/', views.beverages, name='beverages'),
    path('spices/', views.spices, name='spices'),
    path('baby/', views.baby, name='baby'),
    path('health/', views.health, name='health'),
    path('household/', views.household, name='household'),
    path('personal/', views.personal, name='personal'),
    path('pet/', views.pet, name='pet'),
    path('moizakazu/', views.moizakazu, name='moizakazu'),



    path('api/apply-promo-code/', views.apply_promo_code, name='apply_promo_code'),

]
