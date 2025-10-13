# events/urls.py
from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('events/', views.event_list, name='event_list'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    path('events/create/', views.event_create, name='event_create'),
    path('events/<int:pk>/update/', views.event_update, name='event_update'),
    path('events/<int:pk>/delete/', views.event_delete, name='event_delete'),

    path('events/<int:event_id>/ticketclasses/', views.ticketclass_list, name='ticketclass_list'),
    path('events/<int:event_id>/ticketclasses/create/', views.ticketclass_create, name='ticketclass_create'),
    path('events/<int:event_id>/ticketclasses/<int:pk>/update/', views.ticketclass_update, name='ticketclass_update'),
    path('events/<int:event_id>/ticketclasses/<int:pk>/delete/', views.ticketclass_delete, name='ticketclass_delete'),

    path('events/<int:event_id>/exhibitors/', views.exhibitor_list, name='exhibitor_list'),
    path('events/<int:event_id>/exhibitors/create/', views.exhibitor_create, name='exhibitor_create'),
    path('events/<int:event_id>/exhibitors/<int:pk>/update/', views.exhibitor_update, name='exhibitor_update'),
    path('events/<int:event_id>/exhibitors/<int:pk>/delete/', views.exhibitor_delete, name='exhibitor_delete'),

    path('events/<int:event_id>/exhibitors/<int:exhibitor_id>/ticket-allocations/', views.ticket_allocation_list, name='ticket_allocation_list'),
    path('exhibitors/<int:exhibitor_id>/ticket-allocations/create/', views.ticket_allocation_create, name='ticket_allocation_create'),
    path('exhibitors/<int:exhibitor_id>/ticket-allocations/<int:pk>/update/', views.ticket_allocation_update, name='ticket_allocation_update'),
    path('exhibitors/<int:exhibitor_id>/ticket-allocations/<int:pk>/delete/', views.ticket_allocation_delete, name='ticket_allocation_delete'),

    path('events/<int:event_id>/exhibitors/<int:exhibitor_id>/team-members/', views.teammember_list, name='teammember_list'),
    path('exhibitors/<int:exhibitor_id>/team-members/create/', views.teammember_create, name='teammember_create'),
    path('exhibitors/<int:exhibitor_id>/team-members/<int:pk>/update/', views.teammember_update, name='teammember_update'),
    path('exhibitors/<int:exhibitor_id>/team-members/<int:pk>/delete/', views.teammember_delete, name='teammember_delete'),
]
