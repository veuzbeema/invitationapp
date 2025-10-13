from django.urls import path
from . import views

app_name = 'invitations'

urlpatterns = [
    path('invitations/upload/', views.file_upload_view, name='file_upload'),
    path('invitations/', views.invitation_list_view, name='invitation_list'),
    path('send-personalized/', views.send_personalized_invitation, name='send_personalized_invitation'),
    path('send-bulk-personalized/', views.send_bulk_personalized_invitation, name='send_bulk_personalized_invitation'),
    path('invitations/list/', views.invitation_list, name='invitation_list'),
    path('edit/', views.edit_invitation, name='edit_invitation'),
    
    path('invite/<str:invitation_key>/', views.invite_landing, name='invite_landing'),
    path('register/<str:invitation_key>/', views.invite_register, name='invite_register'),


    # path('create/', views.invitation_create, name='invitation_create'),
    # path('<int:pk>/', views.invitation_detail, name='invitation_detail'),
    # path('<int:pk>/edit/', views.invitation_edit, name='invitation_edit'),
    # path('<int:pk>/delete/', views.invitation_delete, name='invitation_delete'),
]