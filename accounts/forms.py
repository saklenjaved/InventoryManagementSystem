from django import forms
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'phone', 'address', 'city', 'state']


class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput, min_length=6)
    email = forms.EmailField()
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    phone = forms.CharField(max_length=100)
    address = forms.CharField(widget=forms.Textarea)
    city = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100)

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('That username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('That email is already registered.')
        return email

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            email=data['email'],
            role=data['role'],
        )
        UserProfile.objects.create(
            user=user,
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data['phone'],
            address=data['address'],
            city=data['city'],
            state=data['state'],
        )
        return user
