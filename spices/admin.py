from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Category, Product, ProductVariant, Review, Order, OrderItem, Payment, ContactMessage

# Admin Site Branding
admin.site.site_header = "Lathriya Spices Administration"
admin.site.site_title = "Lathriya Spices Admin Portal"
admin.site.index_title = "Store & Payment Management Dashboard"

from django.db import models

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('image_preview', 'name', 'slug', 'product_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    fields = ('name', 'slug', 'image', 'image_url', 'description')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(products_count=models.Count('products'))

    def image_preview(self, obj):
        url = obj.get_image_url()
        return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: contain; border-radius: 8px; border: 1px solid #ddd;" />', url)
    image_preview.short_description = "Image"

    def product_count(self, obj):
        count = getattr(obj, 'products_count', obj.products.count())
        return format_html('<span style="font-weight: bold; color: #1B5E20;">{} Spices</span>', count)
    product_count.short_description = "Total Spices"

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('weight', 'price', 'stock_quantity', 'is_default')

class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ('user', 'rating', 'comment', 'created_at')
    can_delete = True

    def has_add_permission(self, request, obj=None):
        return False

from django.forms import Textarea

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('image_preview', 'name', 'category', 'starting_price_display', 'stock_quantity', 'variant_stocks_display', 'review_stats', 'is_featured', 'created_at')
    list_filter = ('category', 'is_featured', 'created_at')
    search_fields = ('name', 'description', 'slug')
    list_editable = ('is_featured', 'stock_quantity')
    prepopulated_fields = {'slug': ('name',)}
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 3, 'cols': 60, 'style': 'height: 75px;'})}
    }
    fieldsets = (
        ('General Info', {
            'fields': ('name', 'slug', 'category', 'price_notice', 'is_featured', 'stock_quantity')
        }),
        ('Product Information & Tabs', {
            'fields': ('description', 'benefits', 'ingredients', 'storage_info')
        }),
        ('Product Images', {
            'fields': ('image', 'image_side', 'image_package', 'image_url')
        }),
    )
    inlines = [ProductVariantInline, ReviewInline]
    ordering = ('-created_at',)
    list_select_related = ('category',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category').prefetch_related('variants', 'reviews')

    def image_preview(self, obj):
        url = obj.get_image_url()
        return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: contain; border-radius: 8px; border: 1px solid #ddd;" />', url)
    image_preview.short_description = "Image"

    def starting_price_display(self, obj):
        return format_html('<span style="font-weight: bold; color: #B8860B;">₹{}</span>', obj.starting_price)
    starting_price_display.short_description = "From"

    def variant_stocks_display(self, obj):
        variants = list(obj.variants.all())
        if not variants:
            return format_html('<span style="color: #999;">No variants</span>')
        items = []
        for v in variants:
            badge_color = "#D32F2F" if v.stock_quantity <= 5 else ("#E65100" if v.stock_quantity <= 10 else "#1B5E20")
            items.append(f'<b>{v.weight}:</b> <span style="color: {badge_color}; font-weight: bold;">{v.stock_quantity} left</span>')
        return format_html("<br/>".join(items))
    variant_stocks_display.short_description = "Variant Stock Breakdown"

    def review_stats(self, obj):
        avg = obj.avg_rating
        count = obj.review_count
        if count == 0:
            return format_html('<span style="color: #999;">No reviews</span>')
        return format_html('<span style="color: #FFC107;">★</span> {} <span style="color: #999;">({})</span>', avg, count)
    review_stats.short_description = "Rating"

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'quantity', 'price', 'item_subtotal')
    can_delete = False

    def item_subtotal(self, obj):
        if obj.quantity and obj.price:
            return f"₹{obj.quantity * obj.price}"
        return "₹0.00"
    item_subtotal.short_description = "Subtotal"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_info', 'phone', 'total_amount_display', 'status_badge', 'tracking_number', 'razorpay_order_id', 'created_at')
    list_editable = ('tracking_number',)
    list_filter = ('status', 'state', 'created_at')
    search_fields = ('id', 'order_number', 'first_name', 'last_name', 'email', 'phone', 'razorpay_order_id', 'tracking_number', 'pincode')
    inlines = [OrderItemInline]
    readonly_fields = ('order_number_field', 'created_at', 'updated_at', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'resend_email_button')
    actions = ['mark_as_paid', 'mark_as_cancelled']
    ordering = ('-created_at',)
    list_select_related = ('user',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('items')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:order_id>/resend-email/', self.admin_site.admin_view(self.resend_email_view), name='order_resend_email'),
        ]
        return custom_urls + urls

    def resend_email_view(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id)
        if not order.tracking_number or not order.tracking_number.strip():
            self.message_user(request, "⚠️ Cannot send email: Please add a Tracking Number first and save.", level='WARNING')
        else:
            from spices.services.email_service import send_order_dispatched_email
            send_order_dispatched_email(order)
            self.message_user(
                request,
                f"✅ Dispatch email with tracking ({order.tracking_number}) and PDF receipt has been sent to {order.email}!"
            )
        return HttpResponseRedirect(reverse('admin:spices_order_change', args=[order_id]))

    def resend_email_button(self, obj):
        if obj.pk and obj.tracking_number and obj.tracking_number.strip():
            url = reverse('admin:order_resend_email', args=[obj.pk])
            return format_html(
                '<a class="button" style="background-color: #1B5E20; color: white; padding: 9px 18px; border-radius: 6px; text-decoration: none; font-weight: 700; display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.15);" href="{}">'
                '✉️ Re-send Dispatch Email & Receipt to Customer'
                '</a>',
                url
            )
        return format_html('<span style="color: #888; font-style: italic;">Enter and save a tracking number above to enable re-sending email.</span>')
    resend_email_button.short_description = "Email Notification"

    def order_number_field(self, obj):
        return format_html('<span style="font-weight: 900; font-size: 16px; color: #1B5E20; letter-spacing: 1px;">{}</span>', obj.display_order_id)
    order_number_field.short_description = "Order Reference No"

    fieldsets = (
        ('Customer Info', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Shipping Details', {
            'fields': ('address', 'district', 'state', 'pincode')
        }),
        ('Order, Payment & Tracking', {
            'fields': ('order_number_field', 'total_amount', 'status', 'tracking_number', 'resend_email_button', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def order_number(self, obj):
        return format_html('<strong style="color: #1B5E20; letter-spacing: 0.5px;">{}</strong>', obj.display_order_id)
    order_number.short_description = "Order No"

    def customer_info(self, obj):
        return format_html('<strong>{} {}</strong><br><small style="color: #666;">{}</small>', obj.first_name, obj.last_name, obj.email)
    customer_info.short_description = "Customer"

    def total_amount_display(self, obj):
        return format_html('<span style="font-weight: bold; color: #1B5E20;">₹{}</span>', obj.total_amount)
    total_amount_display.short_description = "Total Amount"

    def status_badge(self, obj):
        colors = {
            'PAID': '#2e7d32',
            'PENDING': '#ed6c02',
            'FAILED': '#d32f2f',
            'CANCELLED': '#757575',
        }
        bg_color = colors.get(obj.status, '#757575')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 11px;">{}</span>',
            bg_color, obj.status
        )
    @admin.action(description="Mark selected orders as PAID")
    def mark_as_paid(self, request, queryset):
        queryset.update(status='PAID')
        self.message_user(request, "Selected orders marked as PAID.")

    @admin.action(description="Mark selected orders as CANCELLED")
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='CANCELLED')
        self.message_user(request, "Selected orders marked as CANCELLED.")

    @admin.action(description="📧 Re-send Dispatch Email & PDF Receipt to Selected Orders")
    def resend_dispatch_email(self, request, queryset):
        from spices.services.email_service import send_order_dispatched_email
        sent_count = 0
        skipped_count = 0
        for order in queryset:
            if order.tracking_number and order.tracking_number.strip():
                send_order_dispatched_email(order)
                sent_count += 1
            else:
                skipped_count += 1

        if sent_count > 0:
            self.message_user(request, f"Successfully queued dispatch email & PDF receipt for {sent_count} order(s).")
        if skipped_count > 0:
            self.message_user(request, f"Skipped {skipped_count} order(s) because no tracking number is assigned yet.", level='WARNING')

    actions = ['mark_as_paid', 'mark_as_cancelled', 'resend_dispatch_email']

    def save_model(self, request, obj, form, change):
        previous_tracking = None
        if change and obj.pk:
            try:
                previous_obj = Order.objects.get(pk=obj.pk)
                previous_tracking = (previous_obj.tracking_number or '').strip()
            except Order.DoesNotExist:
                previous_tracking = None

        super().save_model(request, obj, form, change)

        current_tracking = (obj.tracking_number or '').strip()
        # If tracking number was newly added or changed and is not empty
        if current_tracking and current_tracking != previous_tracking:
            from spices.services.email_service import send_order_dispatched_email
            send_order_dispatched_email(obj)
            self.message_user(
                request,
                f"Consignment tracking email with PDF receipt queued for {obj.email} (Tracking: {current_tracking})."
            )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_link', 'user_info', 'amount_display', 'status_badge', 'razorpay_payment_id', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'order__id', 'user__email', 'razorpay_payment_id', 'razorpay_order_id')
    readonly_fields = ('order', 'user', 'amount', 'status', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'created_at')
    ordering = ('-created_at',)
    list_select_related = ('order', 'user')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('order', 'user')

    def order_link(self, obj):
        return format_html('<a href="/admin/spices/order/{}/change/" style="font-weight: bold; color: #1B5E20;">Order #{}</a>', obj.order.id, obj.order.display_order_id)
    order_link.short_description = "Order"

    def user_info(self, obj):
        email = obj.user.email if obj.user else "Guest"
        return format_html('<span>{}</span>', email)
    user_info.short_description = "User"

    def amount_display(self, obj):
        return format_html('<span style="font-weight: bold; color: #B8860B;">₹{}</span>', obj.amount)
    amount_display.short_description = "Amount"

    def status_badge(self, obj):
        colors = {
            'SUCCESS': '#2e7d32',
            'INITIATED': '#ed6c02',
            'FAILED': '#d32f2f',
        }
        bg_color = colors.get(obj.status, '#757575')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 11px;">{}</span>',
            bg_color, obj.status
        )
    status_badge.short_description = "Status"

# Custom User Admin with Orders Count and Clean View
admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_orders_count', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(orders_count=models.Count('orders'))

    def user_orders_count(self, obj):
        count = getattr(obj, 'orders_count', obj.orders.count())
        return format_html('<span style="font-weight: bold; color: #1B5E20;">{} Orders</span>', count)
    user_orders_count.short_description = "Orders Placed"

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_superuser:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'short_message', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'phone', 'message')
    list_editable = ('is_read',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def short_message(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    short_message.short_description = "Message Preview"
