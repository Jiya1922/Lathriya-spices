from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, db_index=True)
    image_url = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        indexes = [
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name

    def get_image_url(self):
        if self.image:
            return self.image.url
        if self.image_url:
            if self.image_url.startswith('http://') or self.image_url.startswith('https://') or self.image_url.startswith('/'):
                return self.image_url
            return f"/static/{self.image_url}"

        # Dynamic slug mapping to specific category spice images
        slug_image_map = {
            'cardamom': '/static/images/categries/cardmom.jpg',
            'pepper': '/static/images/categries/pepper.jpg',
            'black-pepper': '/static/images/categries/pepper.jpg',
            'cloves': '/static/images/categries/cloves.jpg',
            'nutmeg': '/static/images/categries/nutmeg.jpg',
        }
        if self.slug in slug_image_map:
            return slug_image_map[self.slug]

        # Fallback to first product's image in this category if available
        first_product = self.products.first()
        if first_product:
            return first_product.get_image_url()

        return "/static/images/main_logo.png"

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    benefits = models.TextField(blank=True, null=True, help_text="Product health benefits (Admin editable)")
    ingredients = models.TextField(blank=True, null=True, help_text="Product ingredients list (Admin editable)")
    storage_info = models.TextField(blank=True, null=True, help_text="Storage & shelf life instructions (Admin editable)")
    image_url = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='posters/', blank=True, null=True)
    image_side = models.ImageField(upload_to='posters/', blank=True, null=True, help_text="Side view of the product")
    image_package = models.ImageField(upload_to='posters/', blank=True, null=True, help_text="Packaging view of the product")
    is_featured = models.BooleanField(default=False, db_index=True)
    stock_quantity = models.PositiveIntegerField(default=50, help_text="Total available stock quantity (Admin editable)")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['category', 'is_featured']),
        ]

    def __str__(self):
        return self.name

    def get_benefits_list(self):
        """Returns benefits split into a clean list of items regardless of whether typed with commas, bullets, or newlines."""
        if not self.benefits:
            return []
        raw = str(self.benefits).replace('•', '').replace('✔', '').replace('check', '')
        items = []
        for line in raw.split('\n'):
            for item in line.split(','):
                cleaned = item.strip()
                if cleaned:
                    items.append(cleaned)
        return items

    def get_ingredients_list(self):
        """Returns ingredients split into a clean list of items regardless of whether typed with commas, bullets, or newlines."""
        if not self.ingredients:
            return []
        raw = str(self.ingredients).replace('•', '').replace('✔', '').replace('check', '')
        items = []
        for line in raw.split('\n'):
            for item in line.split(','):
                cleaned = item.strip()
                if cleaned:
                    items.append(cleaned)
        return items

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Sync stock with default variant if Product.stock_quantity was directly edited by admin
        if self.pk:
            variants = list(self.variants.all())
            if variants:
                if len(variants) == 1:
                    ProductVariant.objects.filter(pk=variants[0].pk).update(stock_quantity=self.stock_quantity)
                else:
                    def_var = next((v for v in variants if v.is_default), variants[0])
                    if def_var:
                        ProductVariant.objects.filter(pk=def_var.pk).update(stock_quantity=self.stock_quantity)

    def get_image_url(self):
        if self.image:
            return self.image.url
        if self.image_url:
            if self.image_url.startswith('http://') or self.image_url.startswith('https://') or self.image_url.startswith('/'):
                return self.image_url
            return f"/static/{self.image_url}"
        return "/static/images/placeholder.png"

    def get_side_image_url(self):
        if self.image_side:
            return self.image_side.url
        return self.get_image_url()

    def get_package_image_url(self):
        if self.image_package:
            return self.image_package.url
        return self.get_image_url()

    @property
    def default_variant(self):
        """Returns default variant or first variant using in-memory prefetched list."""
        all_v = list(self.variants.all())
        for v in all_v:
            if v.is_default:
                return v
        return all_v[0] if all_v else None

    @property
    def starting_price(self):
        """Lowest variant price using in-memory prefetched list."""
        all_v = list(self.variants.all())
        if all_v:
            return min(v.price for v in all_v)
        return 0

    @property
    def avg_rating(self):
        """Average rating using in-memory prefetched reviews."""
        revs = list(self.reviews.all())
        if revs:
            return round(sum(r.rating for r in revs) / len(revs), 1)
        return 0

    @property
    def review_count(self):
        """Review count using in-memory prefetched reviews."""
        return len(self.reviews.all())

    @property
    def total_stock_quantity(self):
        """Returns live total stock across all active variants."""
        all_v = list(self.variants.all())
        if all_v:
            return sum(v.stock_quantity for v in all_v)
        return self.stock_quantity

    def sync_stock_quantity(self):
        """Recalculates total stock from all variants and updates DB."""
        all_v = list(self.variants.all())
        if all_v:
            total = sum(v.stock_quantity for v in all_v)
            if self.stock_quantity != total:
                Product.objects.filter(pk=self.pk).update(stock_quantity=total)
                self.stock_quantity = total
        return self.stock_quantity


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    weight = models.CharField(max_length=50, help_text="e.g. 50g, 100g, 250g")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=50, help_text="Available stock quantity for this variant (Admin editable)")
    is_default = models.BooleanField(default=False, help_text="Shown first on product page")

    class Meta:
        ordering = ['price']
        unique_together = ('product', 'weight')

    def __str__(self):
        return f"{self.product.name} - {self.weight} @ ₹{self.price}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.product_id:
            total = sum(v.stock_quantity for v in self.product.variants.all())
            Product.objects.filter(pk=self.product_id).update(stock_quantity=total)


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1 to 5 stars"
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}★)"


class Order(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=15, db_index=True)
    address = models.TextField()
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True, help_text="Courier / India Post Tracking Number provided by Admin")
    order_number = models.CharField(max_length=50, blank=True, null=True, unique=True, db_index=True, help_text="Unique non-sequential order reference e.g. LS-849201")
    
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    # Receipt Storage Credentials
    receipt_path = models.CharField(max_length=255, blank=True, null=True, help_text="Supabase storage path e.g. payment-receipts/2026/08/pay_123.pdf")
    receipt_url = models.URLField(max_length=500, blank=True, null=True, help_text="Direct/Presigned Supabase URL to download PDF receipt")

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['razorpay_order_id']),
            models.Index(fields=['email']),
            models.Index(fields=['order_number']),
        ]

    @property
    def display_order_id(self):
        return self.order_number or f"LS-{self.id + 100000}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            import random
            for _ in range(25):
                candidate = f"LS-{random.randint(100000, 999999)}"
                if not Order.objects.filter(order_number=candidate).exists():
                    self.order_number = candidate
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.order_number or self.id} - {self.first_name} {self.last_name} ({self.status})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', db_index=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product_name} (Order #{self.order.id})"

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments', db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default='INITIATED', db_index=True)
    
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['razorpay_payment_id']),
        ]

    def __str__(self):
        return f"Payment #{self.id} for Order #{self.order.id} - {self.status}"


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items', db_index=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    # auto_now_add=True: set ONLY on creation — prevents every cart update from resetting the
    # 15-minute reservation clock, which would allow bots/users to hold stock hostage indefinitely.
    # Call touch_reservation() explicitly when you intentionally want to refresh the timer.
    reserved_at = models.DateTimeField(auto_now_add=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'variant')
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.quantity}x {self.variant}"

    def touch_reservation(self):
        """Explicitly refresh the reservation timer (e.g. on active checkout interaction)."""
        from django.utils import timezone
        CartItem.objects.filter(pk=self.pk).update(reserved_at=timezone.now())


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    @property
    def is_complete(self):
        return bool(
            self.user.first_name and self.user.first_name.strip() and
            self.phone and self.phone.strip() and
            self.address and self.address.strip() and
            self.state and self.state.strip() and
            self.district and self.district.strip() and
            self.pincode and self.pincode.strip()
        )


class ContactMessage(models.Model):
    """Stores customer feedback and contact form submissions."""
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback from {self.name} ({self.email})"


from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.core.exceptions import PermissionDenied

@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    """Automatically creates or saves UserProfile for any User (including Google OAuth users)."""
    if created:
        UserProfile.objects.get_or_create(user=instance)
    else:
        if not hasattr(instance, 'profile'):
            UserProfile.objects.get_or_create(user=instance)

@receiver(pre_delete, sender=User)
def prevent_superuser_deletion(sender, instance, **kwargs):
    """Protects superuser admin account from being deleted from the database."""
    if instance.is_superuser:
        raise PermissionDenied("Superuser admin account is protected and cannot be deleted from the database.")


from django.db.models.signals import post_delete, pre_save

@receiver(post_delete, sender=Product)
def delete_product_images_on_delete(sender, instance, **kwargs):
    """Automatically deletes physical image files from storage when a Product is deleted from DB."""
    for field_name in ['image', 'image_side', 'image_package']:
        file_field = getattr(instance, field_name, None)
        if file_field and file_field.name:
            try:
                file_field.delete(save=False)
            except Exception as e:
                logger.warning(f"Could not delete product image file '{file_field.name}': {e}")

@receiver(post_delete, sender=Category)
def delete_category_images_on_delete(sender, instance, **kwargs):
    """Automatically deletes physical image files from storage when a Category is deleted from DB."""
    if instance.image and instance.image.name:
        try:
            instance.image.delete(save=False)
        except Exception as e:
            logger.warning(f"Could not delete category image file '{instance.image.name}': {e}")

@receiver(pre_save, sender=Product)
def delete_old_product_images_on_change(sender, instance, **kwargs):
    """Deletes old physical image file when a Product image is updated with a new file."""
    if not instance.pk:
        return
    try:
        old_instance = Product.objects.get(pk=instance.pk)
        for field_name in ['image', 'image_side', 'image_package']:
            old_file = getattr(old_instance, field_name, None)
            new_file = getattr(instance, field_name, None)
            if old_file and old_file.name and old_file != new_file:
                old_file.delete(save=False)
    except Product.DoesNotExist:
        pass

@receiver(pre_save, sender=Category)
def delete_old_category_images_on_change(sender, instance, **kwargs):
    """Deletes old physical image file when a Category image is updated with a new file."""
    if not instance.pk:
        return
    try:
        old_instance = Category.objects.get(pk=instance.pk)
        if old_instance.image and old_instance.image.name and old_instance.image != instance.image:
            old_instance.image.delete(save=False)
    except Category.DoesNotExist:
        pass


@receiver(post_delete, sender=Order)
def delete_order_receipt_on_delete(sender, instance, **kwargs):
    """Automatically deletes the PDF receipt file from Supabase Storage when an Order is deleted from DB."""
    if instance.receipt_path:
        from spices.services.supabase_service import delete_receipt_from_supabase
        delete_receipt_from_supabase(instance.receipt_path)


@receiver(post_delete, sender=ProductVariant)
def sync_product_stock_on_variant_delete(sender, instance, **kwargs):
    """Recalculates product total stock when a variant is deleted."""
    if instance.product_id:
        total = sum(v.stock_quantity for v in instance.product.variants.all())
        Product.objects.filter(pk=instance.product_id).update(stock_quantity=total)


