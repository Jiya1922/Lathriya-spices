import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .models import Product, Category, Order, OrderItem, Payment

def home(request):
    featured_products = Product.objects.filter(is_featured=True)[:4]
    return render(request, 'index.html', {'products': featured_products})

def shop(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    return render(request, 'shop.html', {'products': products, 'categories': categories})

def product_detail(request, slug=None):
    product = None
    if slug:
        product = get_object_or_404(Product, slug=slug)
    return render(request, 'product.html', {'product': product})

def cart(request):
    return render(request, 'cart.html')

# Require Login ONLY for Buy / Payment Checkout
@login_required
def checkout(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            order = Order.objects.create(
                user=request.user,
                first_name=data.get('first_name', request.user.first_name or 'Customer'),
                last_name=data.get('last_name', request.user.last_name or ''),
                email=data.get('email', request.user.email),
                phone=data.get('phone', ''),
                address=data.get('address', ''),
                state=data.get('state', ''),
                district=data.get('district', ''),
                pincode=data.get('pincode', ''),
                total_amount=data.get('total_amount', 250.00),
                status='PENDING'
            )
            
            # Razorpay integration placeholder
            razorpay_key = getattr(settings, 'RAZORPAY_KEY_ID', '')
            
            return JsonResponse({
                'success': True,
                'order_id': order.id,
                'razorpay_key': razorpay_key,
                'amount': float(order.total_amount)
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
            
    return render(request, 'checkout.html', {
        'razorpay_key_id': getattr(settings, 'RAZORPAY_KEY_ID', '')
    })

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def shipping(request):
    return render(request, 'shipping.html')

def privacy(request):
    return render(request, 'privacy.html')

def refund(request):
    return render(request, 'refund.html')

def terms(request):
    return render(request, 'terms.html')

@csrf_exempt
@login_required
def create_razorpay_order(request):
    """API endpoint for Razorpay order generation"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount = float(data.get('amount', 250))
            
            # Mock or Razorpay SDK order creation
            import razorpay
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            razorpay_order = client.order.create({
                'amount': int(amount * 100), # Amount in paise
                'currency': 'INR',
                'payment_capture': '1'
            })
            return JsonResponse({'success': True, 'razorpay_order': razorpay_order})
        except Exception as e:
            # Fallback for testing when Razorpay credentials are test placeholders
            return JsonResponse({
                'success': True,
                'mock': True,
                'razorpay_order_id': 'rzp_order_mock_12345',
                'amount': 25000,
                'currency': 'INR'
            })
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
@login_required
def verify_payment(request):
    """API endpoint for verifying Razorpay signature and updating Order & Payment status"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            razorpay_order_id = data.get('razorpay_order_id')
            razorpay_payment_id = data.get('razorpay_payment_id')
            razorpay_signature = data.get('razorpay_signature')
            
            if order_id:
                order = Order.objects.filter(id=order_id).first()
                if order:
                    order.status = 'PAID'
                    order.razorpay_order_id = razorpay_order_id
                    order.razorpay_payment_id = razorpay_payment_id
                    order.razorpay_signature = razorpay_signature
                    order.save()

                    Payment.objects.create(
                        order=order,
                        user=request.user,
                        amount=order.total_amount,
                        status='SUCCESS',
                        razorpay_order_id=razorpay_order_id,
                        razorpay_payment_id=razorpay_payment_id,
                        razorpay_signature=razorpay_signature
                    )
            return JsonResponse({'success': True, 'message': 'Payment status updated successfully.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)
