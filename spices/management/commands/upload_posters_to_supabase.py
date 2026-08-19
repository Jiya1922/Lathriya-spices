import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from spices.models import Product, Category

class Command(BaseCommand):
    help = 'Uploads local spice poster images to Supabase Storage bucket and updates database models'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting poster upload to Supabase Storage...")

        base_dir = settings.BASE_DIR
        static_dir = base_dir / 'static'

        # Upload Product Posters
        products = Product.objects.all()
        uploaded_count = 0

        for product in products:
            if product.image_url and not product.image:
                local_rel_path = product.image_url.lstrip('/')
                local_file_path = static_dir / local_rel_path
                
                if not local_file_path.exists() and local_rel_path.endswith('.jpg'):
                    alt_path = static_dir / (local_rel_path[:-4] + 'g.jpg')
                    if alt_path.exists():
                        local_file_path = alt_path
                        product.image_url = local_rel_path[:-4] + 'g.jpg'

                if local_file_path.exists():
                    file_name = Path(local_file_path).name
                    with open(local_file_path, 'rb') as f:
                        django_file = File(f, name=file_name)
                        product.image.save(file_name, django_file, save=True)
                    uploaded_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Successfully uploaded poster for '{product.name}' -> {product.image.url}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Local file not found for '{product.name}': {local_file_path}"))
            elif product.image:
                # Clean up nested path if needed
                clean_name = product.image.name.replace('posters/posters/posters/', 'posters/').replace('posters/posters/', 'posters/')
                if clean_name != product.image.name:
                    product.image.name = clean_name
                    product.save()
                self.stdout.write(f"Product '{product.name}' image clean URL: {product.image.url}")


        # Upload Category Posters
        categories = Category.objects.all()
        for category in categories:
            if category.image_url and not category.image:
                local_rel_path = category.image_url.lstrip('/')
                local_file_path = static_dir / local_rel_path
                if local_file_path.exists():
                    file_name = Path(local_rel_path).name
                    with open(local_file_path, 'rb') as f:
                        django_file = File(f, name=file_name)
                        category.image.save(file_name, django_file, save=True)
                    self.stdout.write(self.style.SUCCESS(f"Successfully uploaded category image for '{category.name}'"))
            elif category.image:
                clean_name = category.image.name.replace('categories/categories/', 'categories/')
                if clean_name != category.image.name:
                    category.image.name = clean_name
                    category.save()


        self.stdout.write(self.style.SUCCESS(f"Finished uploading posters! Processed {uploaded_count} products."))
