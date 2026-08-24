from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('product/', views.product_detail, name='product'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<str:order_ref>/', views.order_success, name='order_success'),
    path('order/receipt/<str:order_ref>/', views.download_receipt, name='download_receipt'),
    path('profile/', views.profile, name='profile'),

    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('shipping/', views.shipping, name='shipping'),
    path('privacy/', views.privacy, name='privacy'),
    path('refund/', views.refund, name='refund'),
    path('terms/', views.terms, name='terms'),
    
    # Cart API routes
    path('api/cart/add/', views.add_to_cart, name='add_to_cart'),
    path('api/cart/update/', views.update_cart, name='update_cart'),
    path('api/cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('api/cart/clear/', views.clear_cart, name='clear_cart'),

    # Razorpay API routes
    path('api/create-razorpay-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('api/verify-payment/', views.verify_payment, name='verify_payment'),
    path('api/razorpay-webhook/', views.razorpay_webhook, name='razorpay_webhook'),

    # Service worker route to handle sw.js cleanly
    path('sw.js', views.service_worker, name='service_worker'),
]


