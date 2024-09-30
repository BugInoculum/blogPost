from django import forms
from .models import CustomUser


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    user_type = forms.ChoiceField(choices=[('admin', 'Admin'), ('regular', 'Regular')])

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'user_type']
