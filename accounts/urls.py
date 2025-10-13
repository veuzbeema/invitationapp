# accounts/urls.py
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('create-user/', views.create_user_view, name='create_user'),
    path('user-list/', views.user_list_view, name='user_list'),
]