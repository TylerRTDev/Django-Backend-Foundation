"""Verifies the fail-open path in core.cache_dogpile_drf does not
re-execute the view when the wrapped method raises."""
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext


@pytest.mark.django_db
def test_404_does_not_double_execute(client):
    """A 404 should cost one product lookup, not two.

    The decorator catches Exception broadly and then calls the view again
    as its fail-open path. When the original failure WAS the view raising
    Http404, that means the lookup runs twice and raises twice.
    """
    with CaptureQueriesContext(connection) as ctx:
        resp = client.get("/api/products/does-not-exist/")

    assert resp.status_code == 404

    lookups = [q for q in ctx.captured_queries if "products_product" in q["sql"]]
    assert len(lookups) == 1, (
        f"view executed {len(lookups)}x on a 404 — fail-open re-ran it. "
        f"Queries: {[q['sql'] for q in lookups]}"
    )