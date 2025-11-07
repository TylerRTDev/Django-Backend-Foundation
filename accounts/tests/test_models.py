# accounts/tests/test_models.py
import pytest
from accounts.models import User, Profile

@pytest.mark.django_db
def test_user_creation_creates_profile():
    user = User.objects.create_user(email="alice@example.com", password="pass1234")
    assert Profile.objects.filter(user=user).exists()
    assert user.profile  # accessible

@pytest.mark.django_db
def test_full_name_property():
    user = User.objects.create_user(email="bob@example.com", first_name="Bob", last_name="Builder")
    assert user.full_name == "Bob Builder"
