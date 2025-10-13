from django.db import models
from django.contrib.auth.models import AbstractUser
from core.models import TimestampedModel
from enum import Enum
from phonenumber_field.modelfields import PhoneNumberField

class UserType(Enum):
    SUPER_ADMIN = 'super_admin'
    SUB_ADMIN = 'sub_admin'
    COMPANY_ADMIN = 'company_admin'
    EXHIBITOR_TEAM = 'exhibitor_team'

    @classmethod
    def choices(cls):
        return [(key.value, key.name.replace('_', ' ').title()) for key in cls]

class Specialization(Enum):
    SALES = 'sales'
    MARKETING = 'marketing'
    TECHNICAL = 'technical'
    MANAGEMENT = 'management'

    @classmethod
    def choices(cls):
        return [(key.value, key.name.replace('_', ' ').title()) for key in cls]

class User(AbstractUser, TimestampedModel):
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices(),
        default=UserType.EXHIBITOR_TEAM.value,
        db_index=True
    )
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(blank=True, null=True)
    specialization = models.CharField(
        max_length=20,
        choices=Specialization.choices(),
        blank=True,
        null=True
    )
    company_name = models.CharField(max_length=255, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    lead_capture_access = models.BooleanField(default=False)
    lead_export_access = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        permissions = [
            ("can_manage_events", "Can manage events"),
            ("can_manage_exhibitors", "Can manage exhibitors"),
            ("can_manage_invitations", "Can manage invitations"),
            ("can_manage_team_members", "Can manage team members"),
        ]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_user_type_display()})"

    def save(self, *args, **kwargs):
        if self.user_type == UserType.SUPER_ADMIN.value:
            self.is_superuser = True
            self.is_staff = True
            self.lead_capture_access = True
            self.lead_export_access = True
        elif self.user_type == UserType.COMPANY_ADMIN.value:
            self.is_staff = True
            self.lead_capture_access = True
            self.lead_export_access = True
        elif self.user_type in [UserType.SUB_ADMIN.value, UserType.EXHIBITOR_TEAM.value]:
            self.is_superuser = False
            self.is_staff = False
            self.lead_capture_access = False
            self.lead_export_access = False
        super().save(*args, **kwargs)