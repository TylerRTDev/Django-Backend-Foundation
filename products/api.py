import urllib3
import requests
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .serializers import QuoteSerializer


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


QUOTABLE_API = "https://api.quotable.io"


class QuoteViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        """Return a single random quote."""
        try:
            resp = requests.get(f"{QUOTABLE_API}/random", timeout=5, verify=False)
            resp.raise_for_status()
            data = resp.json()
            serializer = QuoteSerializer(
                data={"content": data["content"], "author": data["author"]}
            )
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data)
        except requests.RequestException:
            return Response(
                {
                    "content": "In the middle of difficulty lies opportunity.",
                    "author": "Albert Einstein",
                }
            )

    @action(detail=False, methods=["get"], url_path="batch")
    def batch(self, request):
        """Return N random quotes.

        Query params:
          - count (int): number of quotes to fetch (default 24, max 100).
        """
        count = min(int(request.query_params.get("count", 24)), 100)
        try:
            resp = requests.get(
                f"{QUOTABLE_API}/quotes/random",
                params={"limit": count},
                timeout=5,
                verify=False,
            )
            resp.raise_for_status()
            data = resp.json()
            quotes = [
                {"content": item["content"], "author": item["author"]}
                for item in data
            ]
            serializer = QuoteSerializer(data=quotes, many=True)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data)
        except requests.RequestException:
            fallback = {
                "content": "In the middle of difficulty lies opportunity.",
                "author": "Albert Einstein",
            }
            return Response([fallback] * count)