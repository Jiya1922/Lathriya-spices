from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from spices.models import Product

class Command(BaseCommand):
    help = 'Force re-uploads posters to clean paths in Supabase Storage'

    def handle(self, *args, **kwargs):
        static_dir = settings.BASE_DIR / 'static'
        
        mapping = {
            'cardamom-powder': 'images/products/cardmom-100g.jpg',
            'black-pepper-powder': 'images/products/pepper-100g.jpg',
            'nutmeg-powder': 'images/products/nutmeg-100g.jpg',
        }

        for product in Product.objects.all():
            rel_path = mapping.get(product.slug)
            if rel_path:
                local_path = static_dir / rel_path
                if local_path.exists():
                    self.stdout.write(f"Re-uploading poster for {product.name} from {local_path}...")
                    with open(local_path, 'rb') as f:
                        file_name = local_path.name
                        # Save file to clean location
                        product.image.save(file_name, File(f), save=True)
                    self.stdout.write(self.style.SUCCESS(f"Saved {product.name} -> {product.image.url}"))
