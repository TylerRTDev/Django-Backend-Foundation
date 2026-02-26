# accounts/forms.py
from django import forms
from .models import User, Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["display_name", "bio", "date_of_birth", "timezone", "language", "avatar", "website", "twitter", "instagram"]

class UserNameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name"]

class EmailLoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autocomplete": "email"})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"})
    )