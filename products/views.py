from django.core.paginator import Paginator
from core.cache_dogpile import SWRConfig, dogpile_cache_swr
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import cache_page
from core.htmx import htmx_variant
from .models import Product

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

@dogpile_cache_swr(SWRConfig(ttl=300, lock_ttl=60, stale_grace=150), variant_resolver=htmx_variant)
def product_list(request):
    """
    Full page view. Loads the page normally and includes the grid container.
    HTMX will swap only the grid by calling /products/grid/.
    """
    page_obj = _get_page_obj(request)
    return render(request, "products/product_list.html", {"page_obj": page_obj})


# If you want dogpile protection for the fragment endpoint (recommended):
@dogpile_cache_swr(SWRConfig(ttl=60, lock_ttl=5, stale_grace=30), variant_resolver=htmx_variant)
def product_grid(request):
    """
    Fragment view. Returns ONLY the grid markup (plus pagination controls if you want).
    Safe to cache publicly because it’s the same for all users.
    """
    page_obj = _get_page_obj(request)
    return render(request, "products/_product_grid.html", {"page_obj": page_obj})

@dogpile_cache_swr(SWRConfig(ttl=60, lock_ttl=5, stale_grace=30), variant_resolver=htmx_variant)
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, "products/product_detail.html", {"product": product})