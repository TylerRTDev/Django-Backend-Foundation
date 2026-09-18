"""
Fixtures for product API and cache adapter tests.

Test configuration (from pytest.ini):
    DJANGO_SETTINGS_MODULE = config.settings  (base.py -> SQLite + LocMemCache)
    No Docker, Postgres, or Memcached needed.
"""
import pytest
from products.models import Product


@pytest.fixture
def api_client():
    """DRF API client for anonymous requests."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def auth_client(db):
    """DRF API client authenticated as a regular user."""
    from rest_framework.test import APIClient
    from accounts.models import User
    user = User.objects.create_user(email="alice@example.com", password="pass1234")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def active_product(db):
    """Single active product fixture."""
    return Product.objects.create(
        name="Test Product",
        slug="test-product",
        description="A test product description.",
        price="29.99",
        is_active=True,
    )


@pytest.fixture
def inactive_product(db):
    """Single inactive product — should not appear in list or be retrievable."""
    return Product.objects.create(
        name="Inactive Item",
        slug="inactive-item",
        description="Should not be visible.",
        price="0.00",
        is_active=False,
    )


@pytest.fixture
def product_batch(db):
    """Create 30 active products for pagination tests."""
    return [
        Product.objects.create(
            name=f"Product {i:03d}",
            slug=f"product-{i:03d}",
            description=f"Description for product {i}.",
            price=f"{(i % 20 + 1) * 100 + 99}",
            is_active=True,
        )
        for i in range(30)
    ]


@pytest.fixture
def mock_request_factory():
    """Django/DRF request factory for direct adapter unit tests."""
    from rest_framework.test import APIRequestFactory
    return APIRequestFactory()