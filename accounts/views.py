from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import LoginForm, RegisterForm, UserProfileForm
from .models import User, UserProfile


def _redirect_if_logged_in(request):
    user = request.accounts_user
    if not user:
        return None
    if user.role == 'admin':
        return redirect('inventory:dashboard')
    return redirect('accounts:profile')


def _redirect_after_auth(request, user):
    next_path = request.POST.get('next') or request.GET.get('next')
    if next_path and next_path.startswith('/') and not next_path.startswith('//'):
        return redirect(next_path)
    if user.role == 'admin':
        return redirect('inventory:dashboard')
    return redirect('accounts:profile')


@require_http_methods(['GET', 'POST'])
def login_view(request):
    redirect_response = _redirect_if_logged_in(request)
    if redirect_response:
        return redirect_response

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username'].strip()
            email = form.cleaned_data['email'].strip().lower()
            password = form.cleaned_data['password']
            user = User.objects.filter(
                username__iexact=username,
                email__iexact=email,
            ).first()
            if user and check_password(password, user.password):
                request.session['accounts_user_id'] = user.pk
                messages.success(request, f'Welcome back, {user.username}.')
                return _redirect_after_auth(request, user)
            messages.error(
                request,
                'Invalid username, email, or password.',
            )
    else:
        form = LoginForm()

    return render(
        request,
        'accounts/login.html',
        {
            'form': form,
            'login_next': request.POST.get('next') or request.GET.get('next'),
        },
    )


@require_http_methods(['GET', 'POST'])
def register_view(request):
    redirect_response = _redirect_if_logged_in(request)
    if redirect_response:
        return redirect_response

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Account created. Sign in with your username, email, and password.',
            )
            return redirect('accounts:login')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@require_http_methods(['POST', 'GET'])
def logout_view(request):
    request.session.pop('accounts_user_id', None)
    messages.info(request, 'You have been signed out.')
    return redirect('accounts:login')


@require_http_methods(['GET', 'POST'])
def profile_view(request):
    user = request.accounts_user
    if not user:
        login_url = reverse('accounts:login')
        query = urlencode({'next': request.get_full_path()})
        return redirect(f'{login_url}?{query}')

    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'first_name': user.username,
            'last_name': '',
            'phone': '',
            'address': '',
            'city': '',
            'state': '',
        },
    )

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(
        request,
        'accounts/profile.html',
        {
            'form': form,
            'profile': profile,
            'account': user,
            'is_admin': user.role == 'admin',
        },
    )



# from django.shortcuts import render, redirect
# from django.contrib import messages
# from django.contrib.auth.hashers import check_password
# from .models import User

# def login_view(request):
#     # agar already login hai
#     if request.session.get('user_id'):
#         return redirect('accounts:profile')

#     if request.method == 'POST':
#         username = request.POST.get('username')
#         email = request.POST.get('email')
#         password = request.POST.get('password')

#         user = User.objects.filter(
#             username=username,
#             email=email
#         ).first()

#         if user and check_password(password, user.password):
#             request.session['user_id'] = user.id
#             messages.success(request, "Login successful")
#             return redirect('accounts:profile')
#         else:
#             messages.error(request, "Invalid credentials")

#     return render(request, 'accounts/login.html')

# from .forms import RegisterForm

# def register_view(request):
#     if request.session.get('user_id'):
#         return redirect('accounts:profile')

#     if request.method == 'POST':
#         form = RegisterForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Account created successfully")
#             return redirect('accounts:login')
#     else:
#         form = RegisterForm()

#     return render(request, 'accounts/register.html', {'form': form})


# def logout_view(request):
#     request.session.flush()   # pura session clear
#     messages.success(request, "Logged out")
#     return redirect('accounts:login')


# from .models import UserProfile

# def profile_view(request):
#     user_id = request.session.get('user_id')

#     if not user_id:
#         return redirect('accounts:login')

#     user = User.objects.get(id=user_id)

#     profile, created = UserProfile.objects.get_or_create(
#         user=user,
#         defaults={
#             'first_name': user.username
#         }
#     )

#     if request.method == 'POST':
#         form = UserProfileForm(request.POST, instance=profile)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Profile updated")
#             return redirect('accounts:profile')
#     else:
#         form = UserProfileForm(instance=profile)

#     return render(request, 'accounts/profile.html', {
#         'form': form,
#         'profile': profile,
#         'user': user
#     })