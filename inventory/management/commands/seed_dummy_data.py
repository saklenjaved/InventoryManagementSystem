from decimal import Decimal

from django.core.management.base import BaseCommand

from inventory.models import Category, Product


DEMO = [
    {
        'category': 'Electronics',
        'products': [
            ('Wireless Mouse', 'Ergonomic 2.4 GHz mouse with USB receiver.', '24.99', 48),
            ('USB-C Hub', '7-in-1 hub: HDMI, USB 3.0, SD, power delivery.', '45.00', 22),
            ('Mechanical Keyboard', 'Tenkeyless, brown switches, backlight.', '89.50', 15),
        ],
    },
    {
        'category': 'Office supplies',
        'products': [
            ('A4 Paper Ream', '500 sheets, 80 gsm, bright white.', '6.49', 120),
            ('Ballpoint Pens (box)', 'Pack of 50 blue ink pens.', '12.99', 60),
        ],
    },
    {
        'category': 'Home & kitchen',
        'products': [
            ('Water Bottle 750ml', 'Insulated stainless steel.', '22.00', 40),
            ('Desk Organizer', 'Bamboo compartments.', '18.50', 20),
        ],
    },
]


class Command(BaseCommand):
    help = 'Create demo categories and products for the shop.'

    def handle(self, *args, **options):
        created_cats = 0
        created_prods = 0
        for block in DEMO:
            cat, c_created = Category.objects.get_or_create(name=block['category'])
            if c_created:
                created_cats += 1
            for name, desc, price, qty in block['products']:
                obj, p_created = Product.objects.get_or_create(
                    name=name,
                    category=cat,
                    defaults={
                        'description': desc,
                        'price': Decimal(price),
                        'quantity': qty,
                    },
                )
                if p_created:
                    created_prods += 1
        self.stdout.write(
            self.style.SUCCESS(
                f'Categories +{created_cats}, products +{created_prods}. '
                f'Totals: {Category.objects.count()} categories, {Product.objects.count()} products.'
            )
        )
