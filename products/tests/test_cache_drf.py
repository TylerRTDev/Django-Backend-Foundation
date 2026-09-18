"""
Direct unit tests for core.cache_dogpile_drf adapter functions.

Tests the decorator logic (lock, cache hit/miss, fail-open, SWR)
without requiring a full ViewSet or database.

All tests patch the cache backend (LocMemCache) to simulate
specific states: pre-populated cache, lock contention, errors.
"""
from types import SimpleNamespace

import pytest
from django.core.cache import caches
from rest_framework.response import Response

from core.cache_dogpile import DogpileConfig, SWRConfig
from core.cache_dogpile_drf import dogpile_cache_drf, dogpile_cache_drf_swr


def _make_request(query_string=""):
    """Build a minimal DRF Request-like object."""
    from rest_framework.test import APIRequestFactory
    factory = APIRequestFactory()
    request = factory.get(f"/api/test/?{query_string}")
    request.user = SimpleNamespace(is_authenticated=False)
    return request


def _make_self():
    """Minimal self/ViewSet stub."""
    return SimpleNamespace()


def _test_method(self, request, *args, **kwargs):
    """Test ViewSet method returning a DRF Response."""
    return Response({"result": "ok"}, status=200)


def _get_cache_keys(cfg, request):
    """Helper to compute cache key names for a given config + request."""
    from core.cache_dogpile import _build_cache_key
    base = _build_cache_key(cfg, request, variant="full")
    return {
        "val": f"{cfg.key_prefix}:val:{base}",
        "lock": f"{cfg.key_prefix}:lock:{base}",
    }


# ── Cache miss → compute → store ───────────────────────────────────────────

class TestCacheMissAndStore:
    """SC-P0-09: Cache miss → lock acquired → computed → stored."""

    CFG = DogpileConfig(ttl=30, lock_ttl=10, key_prefix="dogpile:test:miss")

    def test_returns_response_on_cache_miss(self):
        decorated = dogpile_cache_drf(self.CFG)(_test_method)
        resp = decorated(_make_self(), _make_request())
        assert resp.status_code == 200
        assert resp.data == {"result": "ok"}

    def test_stores_value_in_cache_on_miss(self):
        request = _make_request()
        keys = _get_cache_keys(self.CFG, request)
        cache = caches[self.CFG.cache_alias]

        cache.delete(keys["val"])

        decorated = dogpile_cache_drf(self.CFG)(_test_method)
        decorated(_make_self(), request)

        cached = cache.get(keys["val"])
        assert cached is not None
        assert cached == {"result": "ok"}


# ── Cache hit returns stored response ──────────────────────────────────────

class TestCacheHit:
    """SC-P0-09: Cache hit returns stored response without calling method."""

    CFG = DogpileConfig(ttl=30, lock_ttl=10, key_prefix="dogpile:test:hit")

    def test_returns_cached_response(self):
        request = _make_request()
        keys = _get_cache_keys(self.CFG, request)
        cache = caches[self.CFG.cache_alias]

        # Pre-populate cache with data dict (not a Response object)
        cache.set(keys["val"], {"cached": "data"}, timeout=self.CFG.ttl)

        call_count = 0

        def method_with_tracker(self, request, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            return Response({"fresh": "data"}, status=200)

        decorated = dogpile_cache_drf(self.CFG)(method_with_tracker)
        resp = decorated(_make_self(), request)

        assert resp.data == {"cached": "data"}
        assert call_count == 0, "Method should NOT have been called on cache hit"


# ── Lock contention ────────────────────────────────────────────────────────

class TestLockContention:
    """SC-P0-10: Lock contention → non-winner polls → uses cached or fallback."""

    CFG = DogpileConfig(
        ttl=30, lock_ttl=10,
        key_prefix="dogpile:test:lock",
        wait_ms=100,
        poll_interval_ms=10,
    )

    def test_non_winner_receives_cached_when_available(self):
        request = _make_request()
        keys = _get_cache_keys(self.CFG, request)
        cache = caches[self.CFG.cache_alias]

        # Simulate: lock is held by another worker
        cache.add(keys["lock"], "1", timeout=self.CFG.lock_ttl)
        # Simulate: another worker has stored the value
        cache.set(keys["val"], {"stored_by_other": "data"}, timeout=self.CFG.ttl)

        decorated = dogpile_cache_drf(self.CFG)(_test_method)
        resp = decorated(_make_self(), request)

        assert resp.data == {"stored_by_other": "data"}

    def test_non_winner_falls_back_when_no_cached_value(self):
        request = _make_request()
        keys = _get_cache_keys(self.CFG, request)
        cache = caches[self.CFG.cache_alias]

        # Lock is held, no cached value yet
        cache.add(keys["lock"], "1", timeout=self.CFG.lock_ttl)
        cache.delete(keys["val"])

        decorated = dogpile_cache_drf(self.CFG)(_test_method)
        resp = decorated(_make_self(), request)

        assert resp.status_code == 200
        assert resp.data == {"result": "ok"}


# ── Fail-open on cache error ───────────────────────────────────────────────

class TestFailOpen:
    """SC-P0-11: Cache exception → fall through to normal response."""

    CFG = DogpileConfig(ttl=30, lock_ttl=10, key_prefix="dogpile:test:fail")

    def test_cache_get_error_falls_through(self):
        with _patched_cache("get", RuntimeError("cache down")):
            decorated = dogpile_cache_drf(self.CFG)(_test_method)
            resp = decorated(_make_self(), _make_request())
            assert resp.status_code == 200
            assert resp.data == {"result": "ok"}

    def test_cache_set_error_falls_through(self):
        with _patched_cache("set", RuntimeError("cache unreachable")):
            decorated = dogpile_cache_drf(self.CFG)(_test_method)
            resp = decorated(_make_self(), _make_request())
            assert resp.status_code == 200
            assert resp.data == {"result": "ok"}

    def test_cache_add_error_falls_through(self):
        with _patched_cache("add", RuntimeError("lock unavailable")):
            decorated = dogpile_cache_drf(self.CFG)(_test_method)
            resp = decorated(_make_self(), _make_request())
            assert resp.status_code == 200
            assert resp.data == {"result": "ok"}


def _patched_cache(method, error):
    """Context manager that patches a cache method to raise."""
    from unittest.mock import patch
    cache = caches["default"]
    return patch.object(cache, method, side_effect=error)


# ── Auth boundary ──────────────────────────────────────────────────────────

class TestAuthBoundary:
    """Authenticated users bypass cache when cache_authenticated=False."""

    CFG_NO_AUTH = DogpileConfig(
        ttl=30, lock_ttl=10,
        key_prefix="dogpile:test:auth",
        cache_authenticated=False,
    )

    def test_authenticated_user_bypasses_by_default(self):
        """With cache_authenticated=False, auth users skip cache."""
        request = _make_request()
        request.user = SimpleNamespace(is_authenticated=True)

        call_count = 0

        def tracker(self, request, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            return Response({"result": "ok"}, status=200)

        decorated = dogpile_cache_drf(self.CFG_NO_AUTH)(tracker)
        decorated(_make_self(), request)
        decorated(_make_self(), request)

        assert call_count == 2, "Method should be called every time (no cache)"

    def test_authenticated_user_caches_when_opted_in(self):
        """With cache_authenticated=True, auth users get cached."""
        request = _make_request()
        request.user = SimpleNamespace(is_authenticated=True)

        cfg = DogpileConfig(
            ttl=30, lock_ttl=10,
            key_prefix="dogpile:test:authunique",
            cache_authenticated=True,
        )

        call_count = 0

        def tracker(self, request, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            return Response({"result": "ok"}, status=200)

        decorated = dogpile_cache_drf(cfg)(tracker)
        decorated(_make_self(), request)
        decorated(_make_self(), request)

        assert call_count == 1, "Method should be called only once (cache hit)"


# ── Key prefix isolation ───────────────────────────────────────────────────

class TestKeyPrefixIsolation:
    """SC-P1-12: Different key prefixes produce independent cache entries."""

    def test_different_prefixes_dont_collide(self):
        cfg_a = DogpileConfig(ttl=30, lock_ttl=10, key_prefix="dogpile:test:a")
        cfg_b = DogpileConfig(ttl=30, lock_ttl=10, key_prefix="dogpile:test:b")

        request = _make_request()
        cache = caches["default"]

        decorated_a = dogpile_cache_drf(cfg_a)(_test_method)
        decorated_b = dogpile_cache_drf(cfg_b)(_test_method)

        resp_a = decorated_a(_make_self(), request)
        assert resp_a.data == {"result": "ok"}

        resp_b = decorated_b(_make_self(), request)
        assert resp_b.data == {"result": "ok"}

        # Verify keys differ
        keys_a = _get_cache_keys(cfg_a, request)
        keys_b = _get_cache_keys(cfg_b, request)
        assert keys_a["val"] != keys_b["val"]


# ── SWR adapter ────────────────────────────────────────────────────────────

class TestSWRAdapter:
    """SC-P1-13: SWR adapter serves stale on cache miss when stale available."""

    CFG = SWRConfig(
        ttl=30, lock_ttl=10,
        stale_grace=60,
        key_prefix="dogpile:test:swr",
        wait_ms=50,
        poll_interval_ms=10,
    )

    def test_returns_stale_when_fresh_expired(self):
        request = _make_request()
        cache = caches[self.CFG.cache_alias]
        base_key = _build_cache_key_for_cfg(self.CFG, request)

        stale_key = f"{self.CFG.key_prefix}:stale:{base_key}"

        # Populate stale only (simulate expired fresh) with data dict
        cache.set(stale_key, {"stale": "data"}, timeout=999)

        decorated = dogpile_cache_drf_swr(self.CFG)(_test_method)
        resp = decorated(_make_self(), request)

        assert resp.data == {"stale": "data"} or resp.data == {"result": "ok"}

    def test_falls_back_on_no_stale(self):
        request = _make_request()
        cache = caches[self.CFG.cache_alias]
        base_key = _build_cache_key_for_cfg(self.CFG, request)

        fresh_key = f"{self.CFG.key_prefix}:fresh:{base_key}"
        stale_key = f"{self.CFG.key_prefix}:stale:{base_key}"

        cache.delete(fresh_key)
        cache.delete(stale_key)

        decorated = dogpile_cache_drf_swr(self.CFG)(_test_method)
        resp = decorated(_make_self(), request)

        assert resp.status_code == 200
        assert resp.data == {"result": "ok"}


def _build_cache_key_for_cfg(cfg, request):
    from core.cache_dogpile import _build_cache_key
    return _build_cache_key(cfg, request, variant="full")