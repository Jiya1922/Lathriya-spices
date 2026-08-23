import logging
from django.core.management.base import BaseCommand
from spices.models import Order
from spices.services.receipt_service import process_payment_receipt

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Generates PDF receipts and uploads them to Supabase for any existing orders missing a receipt."

    def handle(self, *args, **options):
        orders = Order.objects.filter(status='PAID').filter(receipt_path__isnull=True) | Order.objects.filter(status='PAID').filter(receipt_path='')
        count = orders.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("All PAID orders already have PDF receipts generated."))
            return

        self.stdout.write(f"Found {count} existing order(s) missing PDF receipts. Processing now...")

        processed = 0
        for order in orders:
            try:
                pid = order.razorpay_payment_id or f"pay_order_{order.id}"
                url = process_payment_receipt(order, payment_id=pid, razorpay_order_id=order.razorpay_order_id)
                if url:
                    processed += 1
                    self.stdout.write(self.style.SUCCESS(f"Order #{order.id} -> Receipt generated: {url}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Order #{order.id} failed: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Finished processing {processed}/{count} orders."))
