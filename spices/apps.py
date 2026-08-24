import os
from django.apps import AppConfig
from django.db.models.signals import post_migrate

def sync_social_app_and_site(sender, **kwargs):
    try:
        from django.contrib.sites.models import Site
        from allauth.socialaccount.models import SocialApp

        domain = os.getenv('RENDER_EXTERNAL_HOSTNAME', os.getenv('SITE_DOMAIN', 'lathriya-spices.onrender.com')).strip()
        if domain:
            site, _ = Site.objects.get_or_create(id=1)
            if site.domain != domain:
                site.domain = domain
                site.name = 'Lathriya Spices'
                site.save()

            client_id = os.getenv('GOOGLE_CLIENT_ID', '').strip()
            secret = os.getenv('GOOGLE_CLIENT_SECRET', '').strip()

            if client_id and secret:
                app, _ = SocialApp.objects.get_or_create(provider='google', defaults={'name': 'Google OAuth'})
                app.client_id = client_id
                app.secret = secret
                app.name = 'Google OAuth'
                app.save()
                if site not in app.sites.all():
                    app.sites.add(site)
    except Exception:
        pass

class SpicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'spices'

    def ready(self):
        post_migrate.connect(sync_social_app_and_site, sender=self)
