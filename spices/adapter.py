import logging
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.contrib import messages

logger = logging.getLogger(__name__)

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom AllAuth adapter to safely handle Google OAuth authentication errors without throwing 500 internal server errors."""

    def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None):
        logger.error(f"Google OAuth authentication error: provider={provider}, error={error}, exception={exception}")
        messages.error(request, "Google sign-in could not be completed. Please try signing in again.")
        return redirect('/accounts/login/')
