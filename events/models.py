# events/models.py
from django.db import models
from accounts.models import User, Specialization
from core.models import TimestampedModel
from enum import Enum
from phonenumber_field.modelfields import PhoneNumberField
from django.core.exceptions import ValidationError

class TicketType(Enum):
    VISITOR = 'visitor'
    VIP = 'vip'
    GOLD = 'gold'
    PLATINUM = 'platinum'
    EXHIBITOR = 'exhibitor'

    @classmethod
    def choices(cls):
        return [(key.value, key.name.replace('_', ' ').title()) for key in cls]

class Event(TimestampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_events'
    )

    def __str__(self):
        return self.name

    def clean(self):
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValidationError('End date must be after start date.')

class TicketClass(TimestampedModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_classes')
    name = models.CharField(max_length=100)
    ticket_type = models.CharField(
        max_length=20,
        choices=TicketType.choices(),
        db_index=True
    )
    sale_start = models.DateTimeField()
    sale_end = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_limit = models.PositiveIntegerField()
    available_quantity = models.PositiveIntegerField(editable=False)

    def __str__(self):
        return f"{self.name} ({self.get_ticket_type_display()}) for {self.event.name}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.available_quantity = self.quantity_limit
        super().save(*args, **kwargs)

    def clean(self):
        if self.sale_start and self.sale_end and self.sale_end <= self.sale_start:
            raise ValidationError('Sale end must be after sale start.')

class Exhibitor(TimestampedModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='exhibitors')
    company_name = models.CharField(max_length=255)
    phone_number = PhoneNumberField(blank=True, null=True)
    booth = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.company_name} at {self.event.name}"

class ExhibitorTicketAllocation(TimestampedModel):
    exhibitor = models.ForeignKey(Exhibitor, on_delete=models.CASCADE, related_name='ticket_allocations')
    ticket_class = models.ForeignKey(TicketClass, on_delete=models.CASCADE, related_name='exhibitor_allocations')
    quantity = models.PositiveIntegerField()
    is_paid = models.BooleanField(default=False)

    class Meta:
        unique_together = ('exhibitor', 'ticket_class')

    def __str__(self):
        return f"{self.quantity} {self.ticket_class.name} tickets for {self.exhibitor.company_name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update available_quantity in TicketClass
        ticket_class = self.ticket_class
        allocated = ticket_class.exhibitor_allocations.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
        ticket_class.available_quantity = ticket_class.quantity_limit - allocated
        ticket_class.save()

class TeamMember(TimestampedModel):
    exhibitor = models.ForeignKey(Exhibitor, on_delete=models.CASCADE, related_name='team_members')
    name = models.CharField(max_length=255)
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
    login_access = models.BooleanField(default=False)
    company_admin = models.BooleanField(default=False)
    lead_capture_access = models.BooleanField(default=False)
    lead_export_access = models.BooleanField(default=False)
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_member_profile'
    )

    def __str__(self):
        return f"{self.name} ({self.email}) for {self.exhibitor.company_name}"

    def save(self, *args, **kwargs):
        if not self.company_name:
            self.company_name = self.exhibitor.company_name
        super().save(*args, **kwargs)