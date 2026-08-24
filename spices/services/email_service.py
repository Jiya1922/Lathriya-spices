import os
import logging
import threading
import requests as http_requests
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


def _get_pdf_bytes_for_order(order):
    """
    Retrieves the PDF receipt bytes for the given order.
    
    Guarantees Single PDF, No Duplication:
    1. If order.receipt_path exists in DB → reads the exact same file from Supabase Storage.
    2. If order.receipt_url exists in DB → downloads from the existing receipt URL.
    3. If not in DB yet (fallback) → generates ONCE, uploads to Supabase, and saves
       order.receipt_path + order.receipt_url in DB for all future downloads/emails.
    """
    # 1. Fetch directly from Supabase Storage via stored database receipt_path
    if order.receipt_path:
        try:
            from spices.services.supabase_service import get_s3_client
            bucket_name = os.getenv('SUPABASE_RECEIPTS_BUCKET', 'payment-receipts').strip()
            object_key = order.receipt_path.split('/', 1)[1] if '/' in order.receipt_path else order.receipt_path
            s3 = get_s3_client()
            obj = s3.get_object(Bucket=bucket_name, Key=object_key)
            pdf_data = obj['Body'].read()
            if pdf_data:
                logger.info(f"[EMAIL_PDF] Successfully retrieved existing stored receipt PDF from path '{order.receipt_path}' for Order #{order.id}")
                return pdf_data
        except Exception as s3_err:
            logger.warning(f"[EMAIL_PDF] S3 fetch failed for Order #{order.id} ('{order.receipt_path}'): {s3_err}")

    # 2. Try HTTP download if receipt_url exists
    receipt_url = (order.receipt_url or '').strip()
    if receipt_url:
        try:
            resp = http_requests.get(receipt_url, timeout=15)
            if resp.status_code == 200 and resp.content:
                logger.info(f"[EMAIL_PDF] Reusing existing Supabase receipt PDF for Order #{order.id} (URL: {receipt_url[:60]}...)")
                return resp.content
            else:
                logger.warning(f"[EMAIL_PDF] Could not download receipt from Supabase for Order #{order.id}. Status: {resp.status_code}")
        except Exception as fetch_err:
            logger.warning(f"[EMAIL_PDF] Failed to fetch existing receipt from Supabase for Order #{order.id}: {fetch_err}")

    # 3. Fallback: generate ONCE, upload to Supabase, and store path in DB
    logger.info(f"[EMAIL_PDF] Initializing and persisting PDF receipt for Order #{order.id} into database & Supabase...")
    try:
        from .pdf_service import generate_payment_receipt

        customer_name = f"{order.first_name} {order.last_name}".strip()
        if not customer_name:
            customer_name = order.user.get_full_name() if order.user else "Customer"

        addr_parts = [p.strip() for p in [order.address, order.district, order.state, order.pincode] if p and p.strip()]

        items = [{
            'product_name': item.product_name,
            'quantity': item.quantity,
            'price': float(item.price)
        } for item in order.items.all()]

        pid = order.razorpay_payment_id or f"pay_order_{order.id}"
        rzp_oid = order.razorpay_order_id or f"ORDER-{order.id}"

        pdf_bytes = generate_payment_receipt(
            customer_name=customer_name,
            payment_id=pid,
            razorpay_order_id=rzp_oid,
            items=items,
            total_amount=float(order.total_amount),
            payment_date=order.created_at or timezone.now(),
            payment_status="SUCCESS",
            customer_phone=order.phone,
            customer_address=", ".join(addr_parts)
        )

        if pdf_bytes:
            try:
                from .supabase_service import upload_receipt_to_supabase
                r_path, r_url = upload_receipt_to_supabase(
                    file_data=pdf_bytes,
                    payment_id=pid,
                    created_at=order.created_at
                )
                order.receipt_path = r_path
                order.receipt_url = r_url
                order.save(update_fields=['receipt_path', 'receipt_url'])
                logger.info(f"[EMAIL_PDF] Persisted new receipt to Supabase path '{r_path}' and saved in database for Order #{order.id}")
            except Exception as up_err:
                logger.warning(f"[EMAIL_PDF] Could not upload initial receipt to Supabase: {up_err}")

        return pdf_bytes
    except Exception as pdf_err:
        logger.error(f"[EMAIL_PDF] Fallback PDF generation failed for Order #{order.id}: {pdf_err}", exc_info=True)
        return None


def _send_dispatch_email_worker(order_id, tracking_number):
    """
    Internal worker that runs in a background thread.
    Sends the order dispatch email with tracking info + reused PDF receipt attachment.
    """
    try:
        from spices.models import Order
        order = Order.objects.prefetch_related('items', 'user').get(id=order_id)
    except Exception as e:
        logger.error(f"[EMAIL_ERROR] Failed to fetch Order #{order_id} for dispatch email: {e}")
        return

    recipient_email = (order.email or (order.user.email if order.user else '')).strip()
    if not recipient_email:
        logger.warning(f"[EMAIL_WARNING] No recipient email for Order #{order.id}. Skipping dispatch email.")
        return

    resend_api_key = getattr(settings, 'RESEND_API_KEY', '') or os.environ.get('RESEND_API_KEY', '').strip()
    if not resend_api_key:
        logger.warning(
            f"[EMAIL_WARNING] RESEND_API_KEY not set. Cannot send dispatch email for Order #{order.id}. "
            f"Please add RESEND_API_KEY in your .env file."
        )
        return

    customer_name = f"{order.first_name} {order.last_name}".strip()
    if not customer_name:
        customer_name = order.user.get_full_name() if order.user else "Valued Customer"

    # Build items list for email template
    items_list = []
    for item in order.items.all():
        subtotal = float(item.price) * int(item.quantity)
        items_list.append({
            'product_name': item.product_name,
            'quantity': item.quantity,
            'price': f"{item.price:.2f}",
            'subtotal': f"{subtotal:.2f}"
        })

    # 1. Get PDF bytes (reuses the same Supabase receipt the user downloads in profile)
    pdf_bytes = _get_pdf_bytes_for_order(order)

    # 2. Render HTML Email Template
    context = {
        'order': order,
        'customer_name': customer_name,
        'items': items_list,
    }
    try:
        html_content = render_to_string('emails/order_dispatched.html', context)
    except Exception as tmpl_err:
        logger.error(f"[TEMPLATE_ERROR] Failed to render order_dispatched.html for Order #{order.id}: {tmpl_err}", exc_info=True)
        return

    # 3. Send Email (Supports Gmail SMTP & Resend)
    provider = getattr(settings, 'EMAIL_PROVIDER', 'smtp').strip().lower()
    subject = f"📦 Your Lathriya Spices Order #{order.display_order_id} has been Dispatched! (Tracking: {tracking_number})"
    
    # Mode A: Gmail / Standard Django SMTP
    if provider == 'smtp' or (getattr(settings, 'EMAIL_HOST_USER', '') and getattr(settings, 'EMAIL_HOST_PASSWORD', '')):
        try:
            from django.core.mail import EmailMultiAlternatives
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '') or f"Lathriya Spices <{settings.EMAIL_HOST_USER}>"
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=f"Hello {customer_name},\n\nYour order #{order.display_order_id} has been dispatched.\nConsignment / Tracking Number: {tracking_number}\n\nThank you for choosing Lathriya Spices!",
                from_email=from_email,
                to=[recipient_email]
            )
            msg.attach_alternative(html_content, "text/html")
            
            # Attach PDF receipt (reuses same Supabase receipt)
            if pdf_bytes:
                msg.attach(f"Lathriya_Spices_Receipt_{order.display_order_id}.pdf", pdf_bytes, "application/pdf")
                
            msg.send(fail_silently=False)
            logger.info(f"[SMTP_SUCCESS] Dispatch email sent via Gmail SMTP for Order #{order.display_order_id} to {recipient_email}")
            return
        except Exception as smtp_err:
            logger.error(f"[SMTP_ERROR] Failed to send email via Gmail SMTP for Order #{order.id} to {recipient_email}: {smtp_err}", exc_info=True)
            # If SMTP fails and resend_api_key is available, try fallback to Resend
            if not resend_api_key:
                return

    # Mode B: Resend API
    if resend_api_key:
        try:
            import resend
            resend.api_key = resend_api_key

            from_email = getattr(settings, 'RESEND_FROM_EMAIL', '') or os.environ.get('RESEND_FROM_EMAIL', '').strip()
            if not from_email:
                from_email = "Lathriya Spices <onboarding@resend.dev>"

            email_params = {
                "from": from_email,
                "to": [recipient_email],
                "subject": subject,
                "html": html_content,
            }

            if pdf_bytes:
                email_params["attachments"] = [
                    {
                        "filename": f"Lathriya_Spices_Receipt_{order.display_order_id}.pdf",
                        "content": list(pdf_bytes),
                    }
                ]

            response = resend.Emails.send(email_params)
            logger.info(f"[RESEND_SUCCESS] Dispatch email sent for Order #{order.display_order_id} to {recipient_email}. ID: {response}")
        except Exception as resend_err:
            logger.error(f"[RESEND_ERROR] Failed to send email for Order #{order.id} to {recipient_email}: {resend_err}", exc_info=True)
    else:
        logger.warning(f"[EMAIL_WARNING] No email credentials found (neither Gmail SMTP nor Resend). Skipping email for Order #{order.id}.")


def send_order_dispatched_email(order, async_send=True):
    """
    Trigger the order dispatch email with tracking details and PDF receipt.
    Runs asynchronously by default to keep admin dashboard fast.
    """
    if not order or not order.id or not order.tracking_number:
        logger.warning("send_order_dispatched_email skipped: invalid order or missing tracking_number.")
        return

    tracking_clean = str(order.tracking_number).strip()
    if not tracking_clean:
        return

    if async_send:
        email_thread = threading.Thread(
            target=_send_dispatch_email_worker,
            args=(order.id, tracking_clean),
            daemon=True
        )
        email_thread.start()
    else:
        _send_dispatch_email_worker(order.id, tracking_clean)
