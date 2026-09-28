import urllib3
import requests
from django.core.paginator import Paginator
from core.cache_dogpile import DogpileConfig, SWRConfig, dogpile_cache_swr, dogpile_cache
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import cache_page
from core.htmx import htmx_variant
from .models import Product


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


QUOTABLE_API = "https://api.quotable.io"


def _fetch_random_quotes(count=1):
    """Fetch N random quotes from the external API. Falls back to a single repeated quote."""
    try:
        resp = requests.get(
            f"{QUOTABLE_API}/quotes/random",
            params={"limit": count},
            timeout=5,
            verify=False,
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            {"content": item["content"], "author": item["author"]}
            for item in data
        ]
    except requests.RequestException:
        fallback = {
            "content": "In the middle of difficulty lies opportunity.",
            "author": "Albert Einstein",
        }
        return [fallback] * count

# @dogpile_cache_swr(SWRConfig(ttl=60, lock_ttl=10, stale_grace=120), variant_resolver=htmx_variant)
# def product_list(request):
#     qs = (
#         Product.objects
#         .filter(is_active=True)
#         .order_by("-created_at", "-id")
#     )

#     paginator = Paginator(qs, 24)
#     page_obj = paginator.get_page(request.GET.get("page"))

#     return render(request, "products/product_list.html", {"page_obj": page_obj})

# @cache_page(60 * 3)  # Cache the product detail view for 3 minutes
# def product_detail(request, slug):
#     product = get_object_or_404(Product, slug=slug, is_active=True)
#     return render(request, "products/product_detail.html", {"product": product})

def _get_page_obj(request):
    qs = (
        Product.objects
        .filter(is_active=True)
        .order_by("-created_at", "-id")
    )
    paginator = Paginator(qs, 24)
    return paginator.get_page(request.GET.get("page"))

@dogpile_cache(DogpileConfig(ttl=60, lock_ttl=10, wait_ms=50, poll_interval_ms=30, key_prefix="dogpile:products:list"))
# @dogpile_cache_swr(SWRConfig(ttl=300, lock_ttl=60, stale_grace=150), variant_resolver=htmx_variant)
# @cache_page(30)  # Cache the full product list page for 30 seconds (optional, since the grid is cached separately)
def product_list(request):
    """
    Full page view. Loads the page normally and includes the grid container.
    HTMX will swap only the grid by calling /products/grid/.
    """
    page_obj = _get_page_obj(request)
    quotes = _fetch_random_quotes(count=len(page_obj.object_list))
    product_quotes = list(zip(page_obj.object_list, quotes))
    return render(
        request,
        "products/product_list.html",
        {"page_obj": page_obj, "product_quotes": product_quotes},
    )


# If you want dogpile protection for the fragment endpoint (recommended):
@dogpile_cache_swr(SWRConfig(ttl=60, lock_ttl=5, stale_grace=30), variant_resolver=htmx_variant)
# @cache_page(30)  # Cache the product grid fragment for 30 seconds.
def product_grid(request):
    """
    Fragment view. Returns ONLY the grid markup (plus pagination controls if you want).
    Each product card gets a unique random quote.
    """
    page_obj = _get_page_obj(request)
    quotes = _fetch_random_quotes(count=len(page_obj.object_list))
    # Zip products with quotes so each card gets one
    product_quotes = list(zip(page_obj.object_list, quotes))
    return render(
        request,
        "products/_product_grid.html",
        {"page_obj": page_obj, "product_quotes": product_quotes},
    )

@dogpile_cache(DogpileConfig(ttl=180, lock_ttl=10, wait_ms=50, poll_interval_ms=30, key_prefix="dogpile:products:detail"))
# @cache_page(60 * 3)  # Cache the product detail view for 3 minutes
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    quote = _fetch_random_quotes(count=1)[0]
    return render(
        request, "products/product_detail.html", {"product": product, "quote": quote}
    )