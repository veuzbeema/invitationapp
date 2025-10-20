from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, UserType, Specialization
from .forms import UserCreationForm



# Login view
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('accounts:user_list')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'accounts/login.html')

# Logout view
def logout_view(request):
    logout(request)
    return redirect('accounts:login')

# Super Admin required decorator
def super_admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        # if not request.user.is_authenticated or request.user.user_type != UserType.SUPER_ADMIN.value:
        if not request.user.is_authenticated:
            messages.error(request, 'You must be a Super Admin to access this page.')
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return wrapper

# # Super Admin required decorator
# def events_access_required(view_func):
#     def wrapper(request, *args, **kwargs):
#         # if not request.user.is_authenticated or request.user.user_type != UserType.SUPER_ADMIN.value:
#         if not request.user.is_authenticated:
#             messages.error(request, 'You must be a Super Admin to access this page.')
#             return redirect('accounts:login')
#         return view_func(request, *args, **kwargs)
#     return wrapper


# Create user view
# @super_admin_required
def create_user_view(request):
    if request.method == 'POST':
        print('---------------request.POST-----------------', request.POST)
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, f'User {user.email} created successfully.')
            return redirect('accounts:user_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    print('---------------Form.error-----------------', error)
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/create_user.html', {'form': form})

# User list view
@super_admin_required
def user_list_view(request):
    users = User.objects.all().order_by('email')
    return render(request, 'accounts/user_list.html', {'users': users})