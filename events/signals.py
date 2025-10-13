from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User, UserType
from .models import TeamMember

@receiver(post_save, sender=TeamMember)
def create_user_for_team_member(sender, instance, created, **kwargs):
    if created and instance.login_access and not instance.user:
        user = User.objects.create(
            username=instance.email.split('@')[0],
            email=instance.email,
            user_type=UserType.EXHIBITOR_TEAM.value,
            phone_number=instance.phone_number,
            specialization=instance.specialization,
            company_name=instance.company_name,
            position=instance.position,
            lead_capture_access=instance.lead_capture_access,
            lead_export_access=instance.lead_export_access,
            is_active=True
        )
        instance.user = user
        instance.save()