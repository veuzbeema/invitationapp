# accounts/signals.py
from django.contrib.auth.models import Permission
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserType

@receiver(post_save, sender=User)
def assign_permissions(sender, instance, created, **kwargs):
    if created:
        permissions = []
        if instance.user_type == UserType.SUPER_ADMIN.value:
            permissions = Permission.objects.filter(codename__in=[
                'can_manage_events',
                'can_manage_exhibitors',
                'can_manage_invitations',
                'can_manage_team_members'
            ])
        elif instance.user_type == UserType.COMPANY_ADMIN.value:
            permissions = Permission.objects.filter(codename__in=[
                'can_manage_exhibitors',
                'can_manage_invitations',
                'can_manage_team_members'
            ])
        elif instance.user_type == UserType.SUB_ADMIN.value:
            permissions = Permission.objects.filter(codename__in=[
                'can_manage_exhibitors',
                'can_manage_invitations'
            ])
        instance.user_permissions.add(*permissions)