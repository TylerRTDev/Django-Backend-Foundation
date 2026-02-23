from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import cache_page

from .models import Product

@cache_page(60 * 1)  # Cache the product list view for 1 minute
def product_list(request):
    qs = (
        Product.objects
        .filter(is_active=True)
        .order_by("-created_at", "-id")
    )

    paginator = Paginator(qs, 24)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "products/product_list.html", {"page_obj": page_obj})

@cache_page(60 * 3)  # Cache the product detail view for 3 minutes
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, "products/product_detail.html", {"product": product})
