import time
import logging
from django.http import HttpResponse
from django.core.cache import cache

logger = logging.getLogger(__name__)

# In-memory fallback tracking dictionary if cache backend is local memory
_IP_TRACKER = {}

class SecurityAndRateLimitMiddleware:
    """
    Production-ready security middleware providing:
    1. IP & Endpoint Rate Limiting (prevents scraping, brute force, and DOS attacks).
    2. Content Security Policy (CSP) headers compatible with Supabase, Razorpay, Google Auth & CDNs.
    3. Standard HTTP Security Headers (XSS protection, nosniff, SameOrigin frame options, Referrer-Policy).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self.get_client_ip(request)
        path = request.path

        # 1. Rate Limiting Check
        if not self.check_rate_limit(ip, path):
            logger.warning(f"[RATE_LIMIT_EXCEEDED] IP '{ip}' exceeded request limit on '{path}'.")
            return HttpResponse(
                "<h3>429 Too Many Requests</h3><p>Rate limit exceeded. Please wait a minute before retrying.</p>",
                status=429,
                content_type="text/html"
            )

        response = self.get_response(request)

        # 2. Add Content Security Policy (CSP) Header
        # Compatible with Supabase Storage, Razorpay Checkout, Google OAuth & CDNs (Bootstrap, FontAwesome, Google Fonts)
        csp_directives = (
            "default-src 'self' https: data: blob:; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://checkout.razorpay.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com data:; "
            "img-src 'self' data: https: blob: *.supabase.co *.supabase.in; "
            "connect-src 'self' https: *.supabase.co *.supabase.in https://lapi.razorpay.com https://api.razorpay.com; "
            "frame-src 'self' https://api.razorpay.com https://checkout.razorpay.com; "
            "object-src 'none'; "
            "base-uri 'self';"
        )
        response["Content-Security-Policy"] = csp_directives

        # 3. Add Additional HTTP Security Headers
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "SAMEORIGIN"  # Allows Razorpay checkout frame
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response

    def get_client_ip(self, request):
        """Extract client IP handling reverse proxy headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip

    def check_rate_limit(self, ip, path):
        """
        Enforces rate limits:
        - Sensitive endpoints (/api/, /order/receipt/, /checkout/): 60 requests per minute
        - Standard routes: 180 requests per minute
        """
        is_sensitive = any(path.startswith(prefix) for prefix in ['/api/', '/order/receipt/', '/checkout/', '/accounts/'])
        limit = 60 if is_sensitive else 180
        window = 60  # 60 seconds

        cache_key = f"rate_{ip}_{'sensitive' if is_sensitive else 'normal'}"
        now = time.time()

        try:
            val = cache.get(cache_key)
            if val is None:
                cache.set(cache_key, [now], window)
                return True
            
            # Clean timestamps older than 60s
            timestamps = [t for t in val if now - t < window]
            if len(timestamps) >= limit:
                return False
            
            timestamps.append(now)
            cache.set(cache_key, timestamps, window)
            return True
        except Exception:
            # In-memory fallback if Django cache fails
            timestamps = _IP_TRACKER.get(cache_key, [])
            timestamps = [t for t in timestamps if now - t < window]
            if len(timestamps) >= limit:
                return False
            timestamps.append(now)
            _IP_TRACKER[cache_key] = timestamps
            return True
