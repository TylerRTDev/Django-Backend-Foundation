from decimal import Decimal
import random

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from products.models import Product


LOREM = (
    "This is a generic item used for testing performance, caching and pagination. "
    "This description exists to simulate realistic text content and page rendering."
)


class Command(BaseCommand):
    help = "Seed the database with products for local testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--total",
            type=int,
            default=150,
            help="Total number of products to ensure exist (default: 150).",
        )

    def handle(self, *args, **options):
        total = options["total"]

        existing = Product.objects.count()
        if existing >= total:
            self.stdout.write(self.style.SUCCESS(
                f"Seed skipped: {existing} products already exist (>= {total})."
            ))
            return

        to_create = total - existing

        products = []
        start_index = existing + 1

        for i in range(start_index, start_index + to_create):
            name = f"Product {i}"
            slug = slugify(name)

            # Ensure slug uniqueness if anything already exists
            base_slug = slug
            suffix = 1
            while Product.objects.filter(slug=slug).exists():
                suffix += 1
                slug = f"{base_slug}-{suffix}"

            price = Decimal(str(random.randint(500, 5000))) / Decimal("100")  # £5.00–£50.00

            products.append(Product(
                name=name,
                slug=slug,
                description=f"{LOREM}",
                price=price,
                is_active=True,
            ))

        Product.objects.bulk_create(products)

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete: created {to_create} products (total now {Product.objects.count()})."
        ))
