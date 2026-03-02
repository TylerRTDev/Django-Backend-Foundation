from __future__ import annotations
import hashlib
import time
from dataclasses import dataclass
from typing import Callable, Optional
from django.core.cache import caches
from django.http import HttpRequest, HttpResponse
from django.utils.cache import patch_response_headers

@dataclass(frozen=True)
class DogpileConfig:
    cache_alias: str = "default"
    ttl: int = 30                 # seconds for cached response
    lock_ttl: int = 10            # seconds lock lives (short)
    wait_ms: int = 200            # max wait for non-winner
    poll_interval_ms: int = 25    # poll interval while waiting
    key_prefix: str = "dogpile:v1"
    cache_control_public: bool = True
    cache_authenticated: bool = False  # if True, also cache authenticated responses (not recommended) Fale by default to avoid accidentally caching user-specific data.

def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _build_cache_key(cfg: DogpileConfig, request: HttpRequest, *, variant: str = "full") -> str:
    # Include path + querystring + variant. (Variant used for HTMX / partials.)
    raw = f"{cfg.key_prefix}:{variant}:{request.path}?{request.META.get('QUERY_STRING','')}"
    return _hash(raw)

def dogpile_cache(cfg: DogpileConfig, *, variant_resolver: Optional[Callable[[HttpRequest], str]] = None):
    """
    View decorator: cache + stampede protection using cache.add() atomic lock.
    Fail-open: cache backend issues fall through to normal rendering.
    """
    def decorator(view_func: Callable[[HttpRequest], HttpResponse]):
        def wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            # Never globally cache authenticated responses.
            if request.user.is_authenticated and not cfg.cache_authenticated:
                return view_func(request, *args, **kwargs)

            variant = variant_resolver(request) if variant_resolver else "full"
            cache = caches[cfg.cache_alias]

            try:
                base_key = _build_cache_key(cfg, request, variant=variant)
                val_key = f"{cfg.key_prefix}:val:{base_key}"
                lock_key = f"{cfg.key_prefix}:lock:{base_key}"

                cached = cache.get(val_key)
                if cached is not None:
                    return cached

                # Attempt to become the single recomputer.
                got_lock = cache.add(lock_key, "1", timeout=cfg.lock_ttl)

                if got_lock:
                    try:
                        resp = view_func(request, *args, **kwargs)
                        # Store the whole HttpResponse object (works with Memcached pickle serializer).
                        cache.set(val_key, resp, timeout=cfg.ttl)
                        return resp
                    finally:
                        cache.delete(lock_key)

                # Non-winner: short wait & poll for populated cache.
                deadline = time.monotonic() + (cfg.wait_ms / 1000.0)
                while time.monotonic() < deadline:
                    time.sleep(cfg.poll_interval_ms / 1000.0)
                    cached = cache.get(val_key)
                    if cached is not None:
                        return cached

                # Fail-open fallback: just compute normally if winner is slow.
                return view_func(request, *args, **kwargs)

            except Exception:
                # Fail-open: never break the site because of cache/lock issues.
                return view_func(request, *args, **kwargs)

        return wrapped
    return decorator

@dataclass(frozen=True)
class SWRConfig(DogpileConfig):
    stale_grace: int = 60  # extra seconds to keep stale copy

def dogpile_cache_swr(cfg: SWRConfig, *, variant_resolver: Optional[Callable[[HttpRequest], str]] = None):
    def decorator(view_func: Callable[[HttpRequest], HttpResponse]):
        def wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            if request.user.is_authenticated:
                return view_func(request, *args, **kwargs)

            variant = variant_resolver(request) if variant_resolver else "full"
            cache = caches[cfg.cache_alias]

            try:
                base_key = _build_cache_key(cfg, request, variant=variant)
                fresh_key = f"{cfg.key_prefix}:fresh:{base_key}"
                stale_key = f"{cfg.key_prefix}:stale:{base_key}"
                lock_key = f"{cfg.key_prefix}:lock:{base_key}"

                fresh = cache.get(fresh_key)
                if fresh is not None:
                    return fresh

                stale = cache.get(stale_key)

                got_lock = cache.add(lock_key, "1", timeout=cfg.lock_ttl)
                if got_lock:
                    try:
                        resp = view_func(request, *args, **kwargs)
                        cache.set(fresh_key, resp, timeout=cfg.ttl)
                        cache.set(stale_key, resp, timeout=cfg.ttl + cfg.stale_grace)
                        return resp
                    finally:
                        cache.delete(lock_key)

                # Non-winner: serve stale immediately if available
                if stale is not None:
                    return stale

                # No stale available: short wait then fail open
                deadline = time.monotonic() + (cfg.wait_ms / 1000.0)
                while time.monotonic() < deadline:
                    time.sleep(cfg.poll_interval_ms / 1000.0)
                    fresh = cache.get(fresh_key)
                    if fresh is not None:
                        return fresh

                return view_func(request, *args, **kwargs)

            except Exception:
                return view_func(request, *args, **kwargs)

        return wrapped
    return decorator