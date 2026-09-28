"""
DRF Response adapter for the dogpile cache decorator.

Same lock mechanism, fail-open behaviour, and auth boundary as the
view-level adapter (core.cache_dogpile), but adapted for DRF ViewSet
methods returning rest_framework.response.Response objects.

Usage:
    from core.cache_dogpile_drf import dogpile_cache_drf
    from core.cache_dogpile import DogpileConfig

    class ProductViewSet(viewsets.ReadOnlyModelViewSet):
        @dogpile_cache_drf(DogpileConfig(key_prefix="dogpile:api:products"))
        def list(self, request, *args, **kwargs):
            return super().list(request, *args, **kwargs)

Key prefix isolation: use "dogpile:api:..." to avoid collisions with
view-level dogpile keys (which use "dogpile:products:...").
"""
from __future__ import annotations

import time
from typing import Any, Callable, Optional

from django.core.cache import caches
from rest_framework.request import Request
from rest_framework.response import Response

from core.cache_dogpile import DogpileConfig, SWRConfig, _build_cache_key


def dogpile_cache_drf(
    cfg: DogpileConfig,
    *,
    variant_resolver: Optional[Callable[[Request], str]] = None,
) -> Callable:
    """
    ViewSet method decorator: short-wait dogpile cache for DRF Responses.

    On cache miss, the first worker acquires an atomic lock and recomputes.
    Other workers poll briefly for the fresh result, then fall back to
    normal computation if the recomputer is slow.

    Fail-open: cache backend failures fall through to normal computation.
    Authenticated users bypass the shared cache by default.
    """
    def decorator(method: Callable[..., Response]) -> Callable[..., Response]:
        def wrapped(
            self: Any,
            request: Request,
            *args: Any,
            **kwargs: Any,
        ) -> Response:
            # Authenticated users bypass the shared cache.
            if request.user.is_authenticated and not cfg.cache_authenticated:
                resp = method(self, request, *args, **kwargs)
                resp["X-Cache"] = "BYPASS"
                return resp

            variant = variant_resolver(request) if variant_resolver else "full"
            cache = caches[cfg.cache_alias]

            try:
                base_key = _build_cache_key(cfg, request, variant=variant)
                val_key = f"{cfg.key_prefix}:val:{base_key}"
                lock_key = f"{cfg.key_prefix}:lock:{base_key}"

                cached = cache.get(val_key)
                if cached is not None:
                    # Reconstruct Response from cached data
                    resp = Response(cached)
                    resp["X-Cache"] = "HIT"
                    return resp

                # Attempt to become the single recomputer.
                got_lock = cache.add(lock_key, "1", timeout=cfg.lock_ttl)

                if got_lock:
                    try:
                        resp = method(self, request, *args, **kwargs)
                        # Cache the serialized data, not the Response object.
                        # DRF Response cannot be pickled before rendering,
                        # and pickle is the default serializer for Memcached
                        # and LocMemCache backends.
                        #
                        # Defensive, not corrective: today DRF raises Http404
                        # rather than returning a 4xx Response, so this guard
                        # is unreachable. It stays because a future @action
                        # that returns Response(..., status=400) directly would
                        # otherwise cache the error body and replay it as 200
                        # (Response(cached) uses the default status code).
                        if 200 <= resp.status_code < 300:
                            cache.set(val_key, resp.data, timeout=cfg.ttl)
                        resp["X-Cache"] = "MISS"
                        return resp
                    finally:
                        cache.delete(lock_key)

                # Non-winner: short wait and poll for fresh result.
                deadline = time.monotonic() + (cfg.wait_ms / 1000.0)
                while time.monotonic() < deadline:
                    time.sleep(cfg.poll_interval_ms / 1000.0)
                    cached = cache.get(val_key)
                    if cached is not None:
                        # Reconstruct Response from cached data
                        resp = Response(cached)
                        resp["X-Cache"] = "WAIT"
                        return resp

                # Fallback: recompute normally if winner is slow.
                resp = method(self, request, *args, **kwargs)
                resp["X-Cache"] = "BYPASS"
                return resp

            except Exception:
                # Fail-open: never break the API because of cache/lock issues.
                resp = method(self, request, *args, **kwargs)
                resp["X-Cache"] = "BYPASS"
                return resp

        return wrapped
    return decorator


def dogpile_cache_drf_swr(
    cfg: SWRConfig,
    *,
    variant_resolver: Optional[Callable[[Request], str]] = None,
) -> Callable:
    """
    ViewSet method decorator: stale-while-revalidate for DRF Responses.

    On cache miss, serves a stale copy immediately (if available) while
    one worker recomputes in the background. If no stale copy exists,
    falls back to the short-wait polling pattern.

    Fail-open and auth boundary: same as dogpile_cache_drf.
    """
    def decorator(method: Callable[..., Response]) -> Callable[..., Response]:
        def wrapped(
            self: Any,
            request: Request,
            *args: Any,
            **kwargs: Any,
        ) -> Response:
            if request.user.is_authenticated and not cfg.cache_authenticated:
                resp = method(self, request, *args, **kwargs)
                resp["X-Cache"] = "BYPASS"
                return resp

            variant = variant_resolver(request) if variant_resolver else "full"
            cache = caches[cfg.cache_alias]

            try:
                base_key = _build_cache_key(cfg, request, variant=variant)
                fresh_key = f"{cfg.key_prefix}:fresh:{base_key}"
                stale_key = f"{cfg.key_prefix}:stale:{base_key}"
                lock_key = f"{cfg.key_prefix}:lock:{base_key}"

                fresh = cache.get(fresh_key)
                if fresh is not None:
                    # Reconstruct Response from cached data
                    resp = Response(fresh)
                    resp["X-Cache"] = "HIT"
                    return resp

                stale = cache.get(stale_key)

                got_lock = cache.add(lock_key, "1", timeout=cfg.lock_ttl)
                if got_lock:
                    try:
                        resp = method(self, request, *args, **kwargs)
                        # Defensive, not corrective: see dogpile_cache_drf.
                        # Only cache successful responses — a 4xx body cached
                        # and reconstructed as Response(cached) would be
                        # replayed with the default 200 status.
                        if 200 <= resp.status_code < 300:
                            data = resp.data
                            cache.set(fresh_key, data, timeout=cfg.ttl)
                            cache.set(stale_key, data, timeout=cfg.ttl + cfg.stale_grace)
                        resp["X-Cache"] = "MISS"
                        return resp
                    finally:
                        cache.delete(lock_key)

                # Non-winner: serve stale immediately if available.
                if stale is not None:
                    resp = Response(stale)
                    resp["X-Cache"] = "STALE"
                    return resp

                # No stale available: short wait then fail open.
                deadline = time.monotonic() + (cfg.wait_ms / 1000.0)
                while time.monotonic() < deadline:
                    time.sleep(cfg.poll_interval_ms / 1000.0)
                    fresh = cache.get(fresh_key)
                    if fresh is not None:
                        # Reconstruct Response from cached data
                        resp = Response(fresh)
                        resp["X-Cache"] = "WAIT"
                        return resp

                resp = method(self, request, *args, **kwargs)
                resp["X-Cache"] = "BYPASS"
                return resp

            except Exception:
                resp = method(self, request, *args, **kwargs)
                resp["X-Cache"] = "BYPASS"
                return resp

        return wrapped
    return decorator