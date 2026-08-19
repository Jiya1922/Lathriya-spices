from django.core.management.base import BaseCommand
from spices.models import Category, Product

class Command(BaseCommand):
    help = 'Seeds initial category and product data'

    def handle(self, *args, **kwargs):
        c_cardamom, _ = Category.objects.get_or_create(
            name='Cardamom',
            slug='cardamom',
            description='Premium handpicked green cardamom.'
        )
        c_pepper, _ = Category.objects.get_or_create(
            name='Black Pepper',
            slug='pepper',
            description='Fresh Kerala black pepper.'
        )
        c_cloves, _ = Category.objects.get_or_create(
            name='Cloves',
            slug='cloves',
            description='Premium aromatic cloves.'
        )
        c_nutmeg, _ = Category.objects.get_or_create(
            name='Nutmeg',
            slug='nutmeg',
            description='Fresh whole nutmeg.'
        )

        p1, _ = Product.objects.get_or_create(
            slug='cardamom-powder',
            defaults={
                'name': 'Cardamom Powder',
                'category': c_cardamom,
                'price': 250.00,
                'weight': '50g',
                'description': 'Finely ground premium Kerala cardamom with a rich aroma.',
                'image_url': 'images/products/cardmom-100g.jpg',
                'is_featured': True
            }
        )

        p2, _ = Product.objects.get_or_create(
            slug='black-pepper-powder',
            defaults={
                'name': 'Black Pepper Powder',
                'category': c_pepper,
                'price': 200.00,
                'weight': '50g',
                'description': 'Freshly ground black pepper with bold flavour and aroma.',
                'image_url': 'images/products/pepper-100g.jpg',
                'is_featured': True
            }
        )

        p3, _ = Product.objects.get_or_create(
            slug='nutmeg-powder',
            defaults={
                'name': 'Nutmeg Powder',
                'category': c_nutmeg,
                'price': 220.00,
                'weight': '50g',
                'description': 'Premium nutmeg powder made from carefully selected nutmeg.',
                'image_url': 'images/products/nutmeg-100g.jpg',
                'is_featured': True
            }
        )


        self.stdout.write(self.style.SUCCESS('Successfully seeded initial categories and products!'))
