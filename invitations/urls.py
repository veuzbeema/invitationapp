from django.urls import path
from . import views

app_name = 'invitations'

urlpatterns = [
    path('invitations/upload/', views.file_upload_view, name='file_upload'),
    path('invitations/', views.invitation_list_view, name='invitation_list'),
    path('send-personalized/', views.send_personalized_invitation, name='send_personalized_invitation'),
    path('send-bulk-personalized/', views.send_bulk_personalized_invitation, name='send_bulk_personalized_invitation'),
    path('send_private_invitation/', views.send_private_invitation, name='send_private_invitation'),

    
    path('invitations/list/', views.invitation_list, name='invitation_list'),
    path('edit/', views.edit_invitation, name='edit_invitation'),
    
    path('invite/<str:invitation_key>/', views.invite_landing, name='invite_landing'),
    path('register/<str:invitation_key>/', views.invite_register, name='invite_register'),

    path('export/', views.ExportInvitationsView.as_view(), name='export_invitations'),
    path('invitations/<int:pk>/view/', views.invitation_view, name='invitation_view'),
    path('invitations/<int:pk>/get/', views.invitation_get, name='invitation_get'),
    path('invitations/<int:pk>/edit/', views.invitation_edit, name='invitation_edit'),
    path('invitations/<int:pk>/delete/', views.invitation_delete, name='invitation_delete'),

    path('send-bulk-invites/', views.bulk_send_invites, name='send-bulk-invites'),
    path('send-broadcast/<int:pk>/', views.send_broadcast, name='send-broadcas'),
    path('bulk-activate/', views.bulk_activate, name='bulk-activate'),
    path('bulk-deactivate/', views.bulk_deactivate, name='bulk-deactivate'),
    path('bulk-delete/', views.bulk_delete, name='bulk-delete'),

    path('export/', views.export_invitations, name='export_invitations'),
    path('export/status/', views.check_export_status, name='check_export_status'),


   

    # path('create/', views.invitation_create, name='invitation_create'),
    # path('<int:pk>/', views.invitation_detail, name='invitation_detail'),
    # path('<int:pk>/edit/', views.invitation_edit, name='invitation_edit'),
    # path('<int:pk>/delete/', views.invitation_delete, name='invitation_delete'),
]