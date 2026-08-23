import logging
from django.db import transaction
from spices.models import Order, Payment
from .pdf_service import generate_payment_receipt
from .supabase_service import upload_receipt_to_supabase

logger = logging.getLogger(__name__)

def process_payment_receipt(order, payment_id=None, razorpay_order_id=None, force_regenerate=False):
    """
    Orchestrates idempotent PDF receipt generation, Supabase Storage upload, and DB updates.
    
    Idempotency:
    - If receipt_path already exists on the Order record, duplicate generation is skipped unless force_regenerate=True.
    - Safe to call multiple times for the same payment/order.
    
    Returns:
    receipt_url (str) if successful, or None if PDF/Upload failed (payment status remains intact).
    """
    if not order:
        logger.warning("process_payment_receipt called with null order.")
        return None

    pid = payment_id or order.razorpay_payment_id or f"pay_order_{order.id}"
    rzp_oid = f"ORDER-{order.id}"

    # 1. Check Idempotency (Prevent Duplicate Receipts)
    if order.receipt_path and not force_regenerate:
        logger.info(f"[IDEMPOTENCY] Receipt already exists for Order #{order.id} (Payment ID: {pid}). Path: '{order.receipt_path}'. Skipping PDF generation.")
        return order.receipt_url

    # Check if another Order already has this payment_id with a receipt
    existing_receipt = Order.objects.filter(razorpay_payment_id=pid).exclude(receipt_path='').exclude(receipt_path__isnull=True).first()
    if existing_receipt and existing_receipt.id != order.id and existing_receipt.receipt_path:
        logger.info(f"[IDEMPOTENCY] Found existing receipt for Payment ID '{pid}' on Order #{existing_receipt.id}. Skipping duplicate generation.")
        order.receipt_path = existing_receipt.receipt_path
        order.receipt_url = existing_receipt.receipt_url
        order.save(update_fields=['receipt_path', 'receipt_url'])
        return existing_receipt.receipt_url

    logger.info(f"Starting PDF receipt processing for Order #{order.id} (Payment ID: {pid})...")

    # 2. Extract trusted Order Items from Database
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

    customer_phone = getattr(order, 'phone', '') or ''
    if not customer_phone and hasattr(order.user, 'profile'):
        customer_phone = getattr(order.user.profile, 'phone', '') or ''

    addr_parts = [p.strip() for p in [getattr(order, 'address', ''), getattr(order, 'district', ''), getattr(order, 'state', ''), getattr(order, 'pincode', '')] if p and p.strip()]
    customer_address = ", ".join(addr_parts)
    if not customer_address and hasattr(order.user, 'profile'):
        prof = order.user.profile
        prof_parts = [p.strip() for p in [getattr(prof, 'address', ''), getattr(prof, 'district', ''), getattr(prof, 'state', ''), getattr(prof, 'pincode', '')] if p and p.strip()]
        customer_address = ", ".join(prof_parts)

    # 3. Generate PDF Receipt Buffer
    try:
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
    except Exception as pdf_err:
        logger.error(f"[PDF_ERROR] PDF generation failed for Order #{order.id} / Payment ID '{pid}': {pdf_err}", exc_info=True)
        # Payment remains PAID; return None allowing retry later
        return None

    # 4. Upload PDF Receipt to Supabase Storage Bucket ('payment-receipts')
    try:
        receipt_path, receipt_url = upload_receipt_to_supabase(
            file_data=pdf_bytes,
            payment_id=pid,
            created_at=order.created_at
        )
    except Exception as upload_err:
        logger.error(f"[SUPABASE_ERROR] Supabase Storage upload failed for Order #{order.id} / Payment ID '{pid}': {upload_err}", exc_info=True)
        # Payment remains PAID; return None allowing retry later
        return None

    # 5. Persist Receipt Path & URL in Database
    try:
        with transaction.atomic():
            order.receipt_path = receipt_path
            order.receipt_url = receipt_url
            if payment_id and not order.razorpay_payment_id:
                order.razorpay_payment_id = payment_id
            order.save(update_fields=['receipt_path', 'receipt_url', 'razorpay_payment_id'])

            # Also update Payment model if present
            payment_rec = Payment.objects.filter(order=order).first()
            if payment_rec:
                payment_rec.status = 'SUCCESS'
                payment_rec.save()

        logger.info(f"Successfully saved receipt record for Order #{order.id} / Payment ID '{pid}'. URL: {receipt_url}")
        return receipt_url
    except Exception as db_err:
        logger.error(f"[DB_ERROR] Failed to save receipt path to database for Order #{order.id}: {db_err}", exc_info=True)
        return receipt_url
