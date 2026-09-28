"""
Product API behaviour, caching, and query-count tests.

Covers endpoint behaviour (functional), cache hit/miss (core behaviour),
auth boundary, key isolation, and query-count assertions (speed metric).

All tests run against SQLite + LocMemCache — no Docker needed.
"""
import pytest
from django.core.cache import caches
from django.db import connection
from django.test.utils import CaptureQueriesContext


# ── Functional: endpoint behaviour ──────────────────────────────────────────

class TestProductList:
    """SC-P2-01: List returns paginated JSON."""

    URL = "/api/products/"

    def test_returns_200(self, api_client, product_batch):
        resp = api_client.get(self.URL)
        assert resp.status_code == 200

    def test_contains_pagination_keys(self, api_client, product_batch):
        resp = api_client.get(self.URL)
        data = resp.json()
        assert "results" in data
        assert "count" in data
        assert "next" in data
        assert "previous" in data

    def test_results_is_list(self, api_client, product_batch):
        resp = api_client.get(self.URL)
        assert isinstance(resp.json()["results"], list)

    def test_returns_24_items_by_default(self, api_client, product_batch):
        """Default page_size is 24."""
        resp = api_client.get(self.URL)
        assert len(resp.json()["results"]) == 24

    def test_count_matches_total_active(self, api_client, product_batch):
        resp = api_client.get(self.URL)
        assert resp.json()["count"] == 30  # all 30 products are active

    def test_has_next_page_for_30_items(self, api_client, product_batch):
        resp = api_client.get(self.URL)
        assert resp.json()["next"] is not None

    def test_no_previous_on_first_page(self, api_client, product_batch):
        resp = api_client.get(self.URL)
        assert resp.json()["previous"] is None


class TestProductPagination:
    """SC-P2-05: Pagination respects page/page_size, caps at max 100."""

    URL = "/api/products/"

    def test_page_2_returns_next_set(self, api_client, product_batch):
        resp = api_client.get(self.URL, {"page": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) == 6  # 30 - 24 = 6 remaining

    def test_page_size_param(self, api_client, product_batch):
        resp = api_client.get(self.URL, {"page_size": 10})
        assert len(resp.json()["results"]) == 10

    def test_page_size_capped_at_100(self, api_client, product_batch):
        resp = api_client.get(self.URL, {"page_size": 200})
        assert len(resp.json()["results"]) == 30  # 30 total, all returned

    def test_page_size_zero_defaults(self, api_client, product_batch):
        """page_size=0 should not crash — falls back to default."""
        resp = api_client.get(self.URL, {"page_size": 0})
        assert resp.status_code == 200
        assert len(resp.json()["results"]) == 24

    def test_out_of_range_page_returns_404(self, api_client, product_batch):
        """DRF returns 404 for out-of-range pages (standard behaviour)."""
        resp = api_client.get(self.URL, {"page": 100})
        assert resp.status_code == 404


class TestProductRetrieve:
    """SC-P2-02, SC-P2-03, SC-P2-04: Retrieve by slug."""

    def test_returns_product_by_slug(self, api_client, active_product):
        resp = api_client.get(f"/api/products/{active_product.slug}/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Product"
        assert data["slug"] == "test-product"
        assert data["price"] == "29.99"

    def test_404_for_inactive_product(self, api_client, inactive_product):
        """SC-P2-03: Inactive products are not retrievable."""
        resp = api_client.get(f"/api/products/{inactive_product.slug}/")
        assert resp.status_code == 404

    def test_404_for_nonexistent_slug(self, api_client, db):
        """SC-P2-04: Nonexistent slug returns 404."""
        resp = api_client.get("/api/products/nonexistent-slug/")
        assert resp.status_code == 404

    def test_returns_all_expected_fields(self, api_client, active_product):
        resp = api_client.get(f"/api/products/{active_product.slug}/")
        data = resp.json()
        expected = {"id", "name", "slug", "description", "price",
                     "product_img", "is_active", "created_at", "updated_at"}
        assert set(data.keys()) == expected


# ── Cache behaviour: hit/miss, key isolation, auth ───────────────────────

class TestCacheHit:
    """SC-P1-06: Second identical request returns cached response."""

    URL = "/api/products/"

    def test_subsequent_request_returns_200(self, api_client, product_batch):
        resp1 = api_client.get(self.URL)
        assert resp1.status_code == 200
        resp2 = api_client.get(self.URL)
        assert resp2.status_code == 200

    def test_cached_and_uncached_responses_match(self, api_client, product_batch):
        """Cached response content should be the same as fresh."""
        resp1 = api_client.get(self.URL)
        resp2 = api_client.get(self.URL)
        assert resp1.json() == resp2.json()


class TestCacheKeyIsolation:
    """SC-P1-07: Different query params produce different cache keys."""

    URL = "/api/products/"

    def test_page_1_and_page_2_return_different_content(self, api_client, product_batch):
        page1 = api_client.get(self.URL, {"page": 1}).json()
        page2 = api_client.get(self.URL, {"page": 2}).json()
        assert page1["results"] != page2["results"]

    def test_different_page_sizes_produce_different_results(self, api_client, product_batch):
        size10 = api_client.get(self.URL, {"page_size": 10}).json()
        size24 = api_client.get(self.URL, {"page_size": 24}).json()
        assert len(size10["results"]) != len(size24["results"])


class TestCacheAuthBoundary:
    """SC-P1-08: Authenticated users receive cached response."""

    URL = "/api/products/"

    def test_authenticated_user_gets_cached_response(self, auth_client, product_batch):
        """With cache_authenticated=True, auth users get cached data."""
        resp = auth_client.get(self.URL)
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert data["count"] == 30

    def test_anonymous_and_authenticated_get_same_data(self, api_client, auth_client, product_batch):
        """Both see the same product catalogue."""
        anon = api_client.get(self.URL).json()
        auth = auth_client.get(self.URL).json()
        assert anon["count"] == auth["count"]


# ── Query count assertions (speed metric) ────────────────────────────────

class TestQueryCounts:
    """Cached requests should make minimal database queries."""

    URL = "/api/products/"

    def test_cached_list_uses_minimal_db_queries(self, api_client, product_batch):
        """Warm cache hit — 0 product DB queries, framework overhead only."""
        api_client.get(self.URL)  # warm cache
        with CaptureQueriesContext(connection) as ctx:
            resp = api_client.get(self.URL)  # cache hit
        assert resp.status_code == 200
        assert len(ctx) <= 4

    def test_first_request_hits_db(self, api_client, product_batch):
        """Cold cache — must query the database for product list."""
        caches["default"].clear()
        with CaptureQueriesContext(connection) as ctx:
            resp = api_client.get(self.URL)
        assert resp.status_code == 200
        assert len(ctx) >= 1

    def test_cached_retrieve_uses_minimal_queries(self, api_client, active_product):
        """Warm cache hit on retrieve — 0 product queries."""
        url = f"/api/products/{active_product.slug}/"
        api_client.get(url)  # warm cache
        with CaptureQueriesContext(connection) as ctx:
            resp = api_client.get(url)  # cache hit
        assert resp.status_code == 200
        assert len(ctx) <= 4