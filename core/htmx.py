from django.http import HttpRequest

def htmx_variant(request: HttpRequest) -> str:
    # HTMX sets HX-Request: true
    return "hx" if request.headers.get("HX-Request") == "true" else "full"