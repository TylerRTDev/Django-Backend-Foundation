from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Product


def product_list(request):
    qs = (
        Product.objects
        .filter(is_active=True)
        .order_by("-created_at", "-id")
    )

    paginator = Paginator(qs, 24)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "products/product_list.html", {"page_obj": page_obj})


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, "products/product_detail.html", {"product": product})
