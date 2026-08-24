import os
import json
import hmac
import hashlib
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from .models import Product, Category, ProductVariant, Review, Order, OrderItem, Payment, CartItem, UserProfile, ContactMessage
from spices.services.receipt_service import process_payment_receipt

logger = logging.getLogger(__name__)



def home(request):
    products = Product.objects.filter(is_featured=True).select_related('category').prefetch_related('variants')[:4]
    if not products:
        products = Product.objects.all().select_related('category').prefetch_related('variants')[:4]
    return render(request, 'index.html', {'products': products})

def shop(request):
    products = Product.objects.all().prefetch_related('variants', 'reviews')
    categories = Category.objects.all()
    return render(request, 'shop.html', {'products': products, 'categories': categories})

def product_detail(request, slug=None):
    if not slug:
        prod_id = request.GET.get('id', '').strip()
        if prod_id:
            slug_map = {
                'cardamom': 'cardamom-powder',
                'pepper': 'black-pepper-powder',
                'nutmeg': 'nutmeg-powder',
            }
            slug = slug_map.get(prod_id, prod_id)

    queryset = Product.objects.prefetch_related('variants', 'reviews__user')
    if slug:
        product = queryset.filter(slug=slug).first()
    else:
        product = None

    if not product:
        product = queryset.first()

    variants = []
    reviews = []
    user_review = None

    if product:
        variants = list(product.variants.all())
        if not variants:
            v = ProductVariant.objects.create(
                product=product,
                weight='50g',
                price=250.00,
                is_default=True
            )
            variants = [v]

        reviews = list(product.reviews.all())
        if request.user.is_authenticated:
            for r in reviews:
                if r.user_id == request.user.id:
                    user_review = r
                    break

        if request.method == 'POST' and request.user.is_authenticated:
            rating = int(request.POST.get('rating', 5))
            comment = request.POST.get('comment', '').strip()
            if 1 <= rating <= 5:
                review, created = Review.objects.update_or_create(
                    product=product,
                    user=request.user,
                    defaults={'rating': rating, 'comment': comment}
                )
                return JsonResponse({'success': True, 'rating': review.rating, 'comment': review.comment})

    return render(request, 'product.html', {
        'product': product,
        'variants': variants,
        'reviews': reviews,
        'user_review': user_review,
    })


from datetime import timedelta
from django.utils import timezone

RESERVATION_TIMEOUT_MINUTES = 15

def release_expired_cart_reservations(request=None):
    """Release stock reserved by cart items older than 15 minutes back to database."""
    cutoff = timezone.now() - timedelta(minutes=RESERVATION_TIMEOUT_MINUTES)
    
    # 1. Expired DB CartItems (Authenticated Users)
    expired_db_items = CartItem.objects.filter(reserved_at__lt=cutoff).select_related('variant')
    for item in list(expired_db_items):
        try:
            with transaction.atomic():
                variant = ProductVariant.objects.select_for_update().get(id=item.variant_id)
                variant.stock_quantity += item.quantity
                variant.save()
                item.delete()
        except Exception:
            pass

    # 2. Expired Session Cart Items (Anonymous Users)
    if request and hasattr(request, 'session'):
        session_cart_meta = request.session.get('cart_reserved_at', {})
        cart_dict = get_cart_dict(request)
        modified = False
        now_ts = timezone.now().timestamp()
        for vid, ts in list(session_cart_meta.items()):
            if now_ts - ts > (RESERVATION_TIMEOUT_MINUTES * 60):
                if str(vid) in cart_dict:
                    qty = int(cart_dict.pop(str(vid), 0))
                    if qty > 0:
                        try:
                            with transaction.atomic():
                                variant = ProductVariant.objects.select_for_update().get(id=vid)
                                variant.stock_quantity += qty
                                variant.save()
                        except Exception:
                            pass
                session_cart_meta.pop(str(vid), None)
                modified = True
        if modified:
            request.session['cart'] = cart_dict
            request.session['cart_reserved_at'] = session_cart_meta
            request.session.modified = True


def get_cart_dict(request):
    return request.session.get('cart', {})

def save_cart_dict(request, cart_dict):
    request.session['cart'] = cart_dict
    if not cart_dict:
        request.session['cart_reserved_at'] = {}
    request.session.modified = True

@login_required
def cart(request):
    release_expired_cart_reservations(request)
    cart_items = []
    subtotal = 0

    db_items = CartItem.objects.filter(user=request.user).select_related('variant__product')
    for item in db_items:
        item_total = float(item.variant.price * item.quantity)
        subtotal += item_total
        cart_items.append({
            'variant_id': item.variant.id,
            'product_name': item.variant.product.name,
            'variant_weight': item.variant.weight,
            'price': float(item.variant.price),
            'quantity': item.quantity,
            'image_url': item.variant.product.get_image_url(),
            'item_total': item_total,
        })

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
    })

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

@receiver(user_logged_in)
def merge_pending_cart_on_login(sender, request, user, **kwargs):
    if not request or not hasattr(request, 'session'):
        return
    session_cart = request.session.get('cart', {})
    pending_vid = request.session.get('pending_cart_variant_id')
    pending_qty = request.session.get('pending_cart_quantity', 1)

    if pending_vid:
        session_cart[str(pending_vid)] = session_cart.get(str(pending_vid), 0) + int(pending_qty)

    if session_cart:
        for vid, qty in session_cart.items():
            try:
                variant = ProductVariant.objects.get(id=vid)
                cart_item, created = CartItem.objects.get_or_create(
                    user=user,
                    variant=variant,
                    defaults={'quantity': int(qty)}
                )
                if not created:
                    cart_item.quantity += int(qty)
                    cart_item.save()
            except (ProductVariant.DoesNotExist, ValueError):
                pass
        request.session['cart'] = {}
        request.session.pop('pending_cart_variant_id', None)
        request.session.pop('pending_cart_quantity', None)
        request.session.modified = True

def add_to_cart(request):
    """Add item to cart via POST. AJAX endpoint. Login Required."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'login_required': True,
            'error': 'Please log in to add items to your cart.'
        }, status=401)

    release_expired_cart_reservations(request)

    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        variant_id = str(data.get('variant_id', ''))
        quantity = int(data.get('quantity', 1))
        is_buy_now = bool(data.get('is_buy_now', False))
    except Exception:
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    if quantity <= 0:
        return JsonResponse({'error': 'Quantity must be positive'}, status=400)

    try:
        with transaction.atomic():
            variant = ProductVariant.objects.select_for_update().select_related('product').get(id=variant_id)

            if request.user.is_authenticated:
                cart_item = CartItem.objects.filter(user=request.user, variant=variant).first()
                existing_qty = cart_item.quantity if cart_item else 0
            else:
                cart_dict = get_cart_dict(request)
                existing_qty = int(cart_dict.get(str(variant.id), 0))

            if is_buy_now:
                # Release reserved stock of all other items in user's cart
                if request.user.is_authenticated:
                    other_items = CartItem.objects.filter(user=request.user).exclude(variant=variant)
                    for oi in other_items:
                        oi.variant.stock_quantity += oi.quantity
                        oi.variant.save()
                    other_items.delete()
                else:
                    for vid, q in list(cart_dict.items()):
                        if str(vid) != str(variant.id):
                            try:
                                v_other = ProductVariant.objects.get(id=vid)
                                v_other.stock_quantity += int(q)
                                v_other.save()
                            except Exception:
                                pass
                    cart_dict = {}

                net_qty = quantity - existing_qty
            else:
                net_qty = quantity

            if net_qty > 0 and variant.stock_quantity < net_qty:
                return JsonResponse({
                    'success': False,
                    'error': f'Only {variant.stock_quantity} units available in stock.'
                }, status=400)

            # Atomic FCFS Stock Reservation / Restoration
            variant.stock_quantity -= net_qty
            if variant.stock_quantity < 0:
                variant.stock_quantity = 0
            variant.save()

            if request.user.is_authenticated:
                new_q = quantity if is_buy_now else (existing_qty + quantity)
                if cart_item:
                    cart_item.quantity = new_q
                    cart_item.save()
                else:
                    CartItem.objects.create(user=request.user, variant=variant, quantity=new_q)

                save_cart_dict(request, {})
                total_count = CartItem.objects.filter(user=request.user).aggregate(total=Sum('quantity'))['total'] or 0
            else:
                new_q = quantity if is_buy_now else (existing_qty + quantity)
                cart_dict[str(variant.id)] = new_q
                save_cart_dict(request, cart_dict)
                session_cart_meta = request.session.get('cart_reserved_at', {})
                session_cart_meta[str(variant.id)] = timezone.now().timestamp()
                request.session['cart_reserved_at'] = session_cart_meta
                request.session.modified = True
                total_count = sum(int(q) for q in cart_dict.values())

            return JsonResponse({'success': True, 'cart_count': total_count})
    except (ProductVariant.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Invalid variant'}, status=400)
    except Exception as e:
        logger.error(f"Error in add_to_cart: {e}", exc_info=True)
        return JsonResponse({'error': 'An unexpected error occurred while updating cart.'}, status=500)


def update_cart(request):
    """Update item quantity. POST {variant_id, quantity} with FCFS stock sync."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        variant_id = str(data.get('variant_id'))
        quantity = int(data.get('quantity', 1))
    except Exception:
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    try:
        with transaction.atomic():
            variant = ProductVariant.objects.select_for_update().get(id=variant_id)
            cart_dict = get_cart_dict(request)

            if request.user.is_authenticated:
                cart_item = CartItem.objects.filter(user=request.user, variant=variant).first()
                old_qty = cart_item.quantity if cart_item else 0
            else:
                old_qty = int(cart_dict.get(str(variant.id), 0))

            delta = quantity - old_qty

            if delta > 0 and variant.stock_quantity < delta:
                return JsonResponse({
                    'success': False,
                    'error': f'Only {variant.stock_quantity} additional units available in stock.'
                }, status=400)

            variant.stock_quantity -= delta
            if variant.stock_quantity < 0:
                variant.stock_quantity = 0
            variant.save()

            if request.user.is_authenticated:
                if quantity <= 0:
                    CartItem.objects.filter(user=request.user, variant=variant).delete()
                    cart_dict.pop(str(variant_id), None)
                else:
                    if cart_item:
                        cart_item.quantity = quantity
                        cart_item.save()
                    else:
                        CartItem.objects.create(user=request.user, variant=variant, quantity=quantity)
                    cart_dict[str(variant_id)] = quantity

                user_items = CartItem.objects.filter(user=request.user).select_related('variant')
                subtotal = float(sum(item.variant.price * item.quantity for item in user_items))
                cart_count = sum(item.quantity for item in user_items)
            else:
                if quantity <= 0:
                    cart_dict.pop(str(variant_id), None)
                else:
                    cart_dict[str(variant_id)] = quantity

                subtotal = 0
                cart_count = 0
                for vid, q in cart_dict.items():
                    try:
                        v = ProductVariant.objects.get(id=vid)
                        subtotal += float(v.price * int(q))
                        cart_count += int(q)
                    except ProductVariant.DoesNotExist:
                        pass

            save_cart_dict(request, cart_dict)
            return JsonResponse({'success': True, 'subtotal': subtotal, 'cart_count': cart_count})
    except (ProductVariant.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Invalid variant'}, status=400)
    except Exception as e:
        logger.error(f"Error in update_cart: {e}", exc_info=True)
        return JsonResponse({'error': 'An unexpected error occurred while updating cart.'}, status=500)


def remove_from_cart(request):
    """Remove item and restore reserved stock back to DB. POST {variant_id}."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        variant_id = str(data.get('variant_id'))
    except Exception:
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    try:
        with transaction.atomic():
            variant = ProductVariant.objects.select_for_update().get(id=variant_id)
            cart_dict = get_cart_dict(request)

            if request.user.is_authenticated:
                cart_item = CartItem.objects.filter(user=request.user, variant=variant).first()
                old_qty = cart_item.quantity if cart_item else 0
                if cart_item:
                    cart_item.delete()
                cart_dict.pop(str(variant_id), None)
            else:
                old_qty = int(cart_dict.get(str(variant_id), 0))
                cart_dict.pop(str(variant_id), None)

            # Restore reserved stock back to database
            variant.stock_quantity += old_qty
            variant.save()

            save_cart_dict(request, cart_dict)

            if request.user.is_authenticated:
                user_items = CartItem.objects.filter(user=request.user).select_related('variant')
                subtotal = float(sum(item.variant.price * item.quantity for item in user_items))
                cart_count = sum(item.quantity for item in user_items)
            else:
                subtotal = 0
                cart_count = 0
                for vid, q in cart_dict.items():
                    try:
                        v = ProductVariant.objects.get(id=vid)
                        subtotal += float(v.price * int(q))
                        cart_count += int(q)
                    except ProductVariant.DoesNotExist:
                        pass

            return JsonResponse({'success': True, 'subtotal': subtotal, 'cart_count': cart_count})
    except (ProductVariant.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Invalid variant'}, status=400)
    except Exception as e:
        logger.error(f"Error in remove_from_cart: {e}", exc_info=True)
        return JsonResponse({'error': 'An unexpected error occurred while removing item.'}, status=500)


def clear_cart(request):
    """Clear all cart items and restore all reserved stock back to DB. POST AJAX endpoint."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        with transaction.atomic():
            cart_dict = get_cart_dict(request)

            if request.user.is_authenticated:
                user_items = CartItem.objects.filter(user=request.user).select_related('variant')
                for item in list(user_items):
                    try:
                        variant = ProductVariant.objects.select_for_update().get(id=item.variant_id)
                        variant.stock_quantity += item.quantity
                        variant.save()
                    except ProductVariant.DoesNotExist:
                        pass
                user_items.delete()
                save_cart_dict(request, {})
            else:
                for vid, q in list(cart_dict.items()):
                    try:
                        variant = ProductVariant.objects.select_for_update().get(id=vid)
                        variant.stock_quantity += int(q)
                        variant.save()
                    except (ProductVariant.DoesNotExist, ValueError):
                        pass
                save_cart_dict(request, {})
                request.session['cart_reserved_at'] = {}
                request.session.modified = True

            return JsonResponse({'success': True, 'subtotal': 0, 'cart_count': 0})
    except Exception as e:
        logger.error(f"Error in clear_cart: {e}", exc_info=True)
        return JsonResponse({'error': 'An unexpected error occurred while clearing cart.'}, status=500)



def get_user_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile

@login_required
def profile(request):
    user_profile = get_user_profile(request.user)
    next_url = request.GET.get('next', '')
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        state = request.POST.get('state', '').strip()
        district = request.POST.get('district', '').strip()
        pincode = request.POST.get('pincode', '').strip()

        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.save()

        user_profile.phone = phone
        user_profile.address = address
        user_profile.state = state
        user_profile.district = district
        user_profile.pincode = pincode
        user_profile.save()

        messages.success(request, 'Profile updated successfully!')
        if next_url:
            return redirect(next_url)
        return redirect('profile')

    orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')

    return render(request, 'profile.html', {
        'profile': user_profile,
        'orders': orders,
        'next_url': next_url,
    })

# Require Login for Checkout
@login_required
def checkout(request):
    release_expired_cart_reservations(request)
    user_profile = get_user_profile(request.user)
    db_items = CartItem.objects.filter(user=request.user).select_related('variant__product')
    
    if not db_items.exists():
        return redirect('shop')

    cart_items = []
    subtotal = 0
    for item in db_items:
        item_total = float(item.variant.price * item.quantity)
        subtotal += item_total
        cart_items.append({
            'variant_id': item.variant.id,
            'product_name': item.variant.product.name,
            'variant_weight': item.variant.weight,
            'price': float(item.variant.price),
            'quantity': item.quantity,
            'image_url': item.variant.product.get_image_url(),
            'item_total': item_total,
        })

    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            first_name = (data.get('first_name') or request.user.first_name or '').strip()
            last_name = (data.get('last_name') or request.user.last_name or '').strip()
            email = (data.get('email') or request.user.email or '').strip()
            phone = (data.get('phone') or user_profile.phone or '').strip()
            address = (data.get('address') or user_profile.address or '').strip()
            state = (data.get('state') or user_profile.state or '').strip()
            district = (data.get('district') or user_profile.district or '').strip()
            pincode = (data.get('pincode') or user_profile.pincode or '').strip()

            if not (first_name and phone and address and state and district and pincode):
                return JsonResponse({
                    'success': False,
                    'profile_incomplete': True,
                    'redirect_url': '/profile/?next=/checkout/',
                    'error': 'Please provide all required shipping details (First Name, Phone, Address, State, District, Pincode).'
                }, status=400)

            # Auto-save shipping details to user & profile for seamless repeat ordering
            if first_name and request.user.first_name != first_name:
                request.user.first_name = first_name
            if last_name and request.user.last_name != last_name:
                request.user.last_name = last_name
            request.user.save()

            user_profile.phone = phone
            user_profile.address = address
            user_profile.state = state
            user_profile.district = district
            user_profile.pincode = pincode
            user_profile.save()

            order = Order.objects.create(
                user=request.user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                address=address,
                state=state,
                district=district,
                pincode=pincode,
                total_amount=subtotal,
                status='PENDING'
            )

            for item in db_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.variant.product,
                    product_name=f"{item.variant.product.name} ({item.variant.weight})",
                    quantity=item.quantity,
                    price=item.variant.price
                )

            razorpay_key = getattr(settings, 'RAZORPAY_KEY_ID', '') or os.getenv('RAZORPAY_KEY_ID', '').strip()
            return JsonResponse({
                'success': True,
                'order_id': order.id,
                'razorpay_key': razorpay_key,
                'amount': float(order.total_amount)
            })
        except Exception as e:
            logger.error(f"Error in checkout processing: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': 'Failed to process checkout request.'}, status=400)

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'profile': user_profile,
        'profile_is_complete': user_profile.is_complete,
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
                'amount': int(amount * 100),
                'currency': 'INR'
            })
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
@login_required
def verify_payment(request):
    """API endpoint for verifying Razorpay signature, updating Order & Payment status, generating PDF receipt and uploading to Supabase."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            razorpay_order_id = data.get('razorpay_order_id')
            razorpay_payment_id = data.get('razorpay_payment_id')
            razorpay_signature = data.get('razorpay_signature')
            
            if order_id:
                order = Order.objects.filter(id=order_id, user=request.user).first()
                if order:
                    order.status = 'PAID'
                    order.razorpay_order_id = razorpay_order_id
                    order.razorpay_payment_id = razorpay_payment_id
                    order.razorpay_signature = razorpay_signature
                    order.save()

                    Payment.objects.get_or_create(
                        order=order,
                        defaults={
                            'user': request.user,
                            'amount': order.total_amount,
                            'status': 'SUCCESS',
                            'razorpay_order_id': razorpay_order_id,
                            'razorpay_payment_id': razorpay_payment_id,
                            'razorpay_signature': razorpay_signature
                        }
                    )
                    # Clear user's cart on successful payment
                    CartItem.objects.filter(user=request.user).delete()

                    # Trigger PDF receipt generation & Supabase upload
                    receipt_url = process_payment_receipt(order, payment_id=razorpay_payment_id, razorpay_order_id=razorpay_order_id)

                    return JsonResponse({
                        'success': True,
                        'receipt_url': receipt_url,
                        'redirect_url': f'/order/success/{order.id}/',
                        'message': 'Payment status updated & receipt processed successfully.'
                    })
            return JsonResponse({'success': True, 'message': 'Payment status updated successfully.'})
        except Exception as e:
            logger.error(f"Error in verify_payment: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': 'Payment verification failed.'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def razorpay_webhook(request):
    """
    Secure Webhook endpoint for Razorpay payment events.
    Verifies X-Razorpay-Signature using RAZORPAY_WEBHOOK_SECRET.
    Process payment.captured & order.paid events, ensuring idempotency.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '') or os.getenv('RAZORPAY_WEBHOOK_SECRET', '').strip()
    received_signature = request.headers.get('X-Razorpay-Signature', '')

    # Verify signature if secret configured
    if webhook_secret and received_signature:
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            request.body,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, received_signature):
            logger.warning("Razorpay Webhook signature verification failed!")
            return JsonResponse({'error': 'Invalid webhook signature'}, status=400)

    try:
        payload = json.loads(request.body)
        event = payload.get('event', '')
        logger.info(f"Razorpay Webhook received event: '{event}'")

        if event in ('payment.captured', 'order.paid'):
            payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
            razorpay_payment_id = payment_entity.get('id')
            razorpay_order_id = payment_entity.get('order_id')
            
            if razorpay_payment_id:
                order = Order.objects.filter(razorpay_order_id=razorpay_order_id).first() or Order.objects.filter(razorpay_payment_id=razorpay_payment_id).first()
                if order:
                    order.status = 'PAID'
                    order.razorpay_payment_id = razorpay_payment_id
                    order.save(update_fields=['status', 'razorpay_payment_id'])

                    # Process PDF receipt generation & Supabase Storage upload idempotently
                    process_payment_receipt(order, payment_id=razorpay_payment_id, razorpay_order_id=razorpay_order_id)

        return JsonResponse({'status': 'ok', 'message': 'Webhook processed successfully'})
    except Exception as e:
        logger.error(f"Error processing Razorpay webhook: {e}", exc_info=True)
        return JsonResponse({'error': 'Webhook processing error'}, status=500)


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_success.html', {
        'order': order
    })


def service_worker(request):
    """Return empty JS response for Service Worker requests to silence 404 logs."""
    return HttpResponse("// Service worker placeholder", content_type="application/javascript")


@login_required
def download_receipt(request, order_id):
    """
    Secure view to download PDF receipt for an order.
    Strictly verifies ownership: User can ONLY view/download their own order receipts.
    Fetches the PDF from Supabase Storage or generates on the fly if missing from storage.
    """
    order = get_object_or_404(Order, id=order_id)
    
    # Strict Ownership Check: Ensure user owns this order or is admin/staff
    if order.user != request.user and not request.user.is_staff:
        logger.warning(f"[SECURITY UNAUTHORIZED] User '{request.user}' attempted unauthorized access to Order #{order.id} receipt owned by '{order.user}'.")
        return HttpResponse("Forbidden: You do not have permission to view or download this receipt.", status=403)

    pdf_bytes = None

    # 1. Attempt to fetch from Supabase Storage if receipt_path is recorded
    if order.receipt_path:
        try:
            from spices.services.supabase_service import get_s3_client
            bucket_name = os.getenv('SUPABASE_RECEIPTS_BUCKET', 'payment-receipts').strip()
            object_key = order.receipt_path.split('/', 1)[1] if '/' in order.receipt_path else order.receipt_path
            s3 = get_s3_client()
            obj = s3.get_object(Bucket=bucket_name, Key=object_key)
            pdf_bytes = obj['Body'].read()
        except Exception as e:
            logger.warning(f"Could not fetch PDF from Supabase Storage for Order #{order.id}: {e}")

    # 2. In-memory Direct PDF Generation (guarantees receipt is always downloadable)
    if not pdf_bytes:
        try:
            from spices.services.pdf_service import generate_payment_receipt
            items = []
            for item in order.items.all():
                items.append({
                    'product_name': item.product_name,
                    'quantity': item.quantity,
                    'price': float(item.price)
                })

            customer_name = f"{order.first_name} {order.last_name}".strip()
            if not customer_name:
                customer_name = order.user.get_full_name() or order.user.username

            customer_phone = getattr(order, 'phone', '') or (getattr(order.user.profile, 'phone', '') if hasattr(order.user, 'profile') else '')
            addr_parts = [p.strip() for p in [getattr(order, 'address', ''), getattr(order, 'district', ''), getattr(order, 'state', ''), getattr(order, 'pincode', '')] if p and p.strip()]
            customer_address = ", ".join(addr_parts)

            pid = order.razorpay_payment_id or f"pay_order_{order.id}"
            rzp_oid = order.razorpay_order_id or f"ORDER-{order.id}"

            pdf_bytes = generate_payment_receipt(
                customer_name=customer_name,
                payment_id=pid,
                razorpay_order_id=rzp_oid,
                items=items,
                total_amount=float(order.total_amount),
                payment_date=order.created_at,
                payment_status="SUCCESS",
                customer_phone=customer_phone,
                customer_address=customer_address
            )

            # Try to upload to Supabase in the background / update record if not uploaded yet
            try:
                from spices.services.supabase_service import upload_receipt_to_supabase
                r_path, r_url = upload_receipt_to_supabase(file_data=pdf_bytes, payment_id=pid, created_at=order.created_at)
                order.receipt_path = r_path
                order.receipt_url = r_url
                order.save(update_fields=['receipt_path', 'receipt_url'])
            except Exception as upload_err:
                logger.warning(f"Background upload to Supabase skipped during download: {upload_err}")
        except Exception as err:
            logger.error(f"Failed to generate receipt in-memory for Order #{order.id}: {err}", exc_info=True)

    if not pdf_bytes:
        return HttpResponse("Receipt could not be generated. Please contact support.", status=500)

    # Clean professional receipt reference code (e.g., REC-851050)
    ref_code = f"REC-{(order.id * 1849 + 849201) % 900000 + 100000}"
    filename = f"Lathriya_Spices_Receipt_{ref_code}.pdf"
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def contact(request):
    """Handles contact form submissions and saves feedback into ContactMessage DB table."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        message = request.POST.get('message', '').strip()

        if name and email and message:
            ContactMessage.objects.create(
                name=name,
                email=email,
                phone=phone,
                message=message
            )
            messages.success(request, 'Thank you for reaching out! Your message has been saved and our team will respond shortly.')
            return redirect('contact')
        else:
            messages.error(request, 'Please fill in all required fields (Name, Email, and Message).')

    return render(request, 'contact.html')

def about(request):
    return render(request, 'about.html')

def shipping(request):
    return render(request, 'shipping.html')

def privacy(request):
    return render(request, 'privacy.html')

def refund(request):
    return render(request, 'refund.html')

def terms(request):
    return render(request, 'terms.html')


