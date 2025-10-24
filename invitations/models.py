from django.db import models
from core.models import TimestampedModel
from events.models import Event, TicketClass
from enum import Enum

class Invitation(TimestampedModel):
    INVITE_TYPES = [
        ('private_link', 'Private Link'),
        ('personalized', 'Personalized Email'),
    ]

    STATUS_TYPES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('expired', 'Expired'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='invitations')
    title_or_name = models.CharField(max_length=255, null=True, blank=True) 

    email = models.EmailField(blank=True, null=True) 
    invite_type = models.CharField(max_length=50, choices=INVITE_TYPES)
    expiry_date = models.DateTimeField()
    link_limit = models.PositiveIntegerField(default=1) 
    link_count = models.PositiveIntegerField(default=1)  
    registered_count = models.PositiveIntegerField(default=0)
    phone = models.CharField(max_length=20, blank=True, null=True)

    invitation_key = models.CharField(max_length = 50, blank=True, null=True)
    status = models.CharField(max_length=50, default='active',choices=STATUS_TYPES)  
    ticket_class = models.ForeignKey(TicketClass, on_delete=models.SET_NULL, null=True, blank=True)
    personal_message = models.TextField(blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True) 

    def __str__(self):
        return f"Invitation for {self.title_or_name} ({self.invite_type})"
    
class InvitationCSVUpload(models.Model):
    """
    Model to store uploaded CSV files for bulk invitation generation.
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='csv_uploads')
    file = models.FileField(upload_to='invitation_csvs/')
    class Status(Enum):
        PENDING = 'pending'
        PROCESSING = 'processing'
        SUCCESS = 'success'
        FAILED = 'failed'
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processed_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    duplicate_count = models.PositiveIntegerField(default=0)
    processed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='pending')
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"CSV Upload for {self.event} at {self.uploaded_at}"
    

class RegisteredUser(TimestampedModel):
    invitation = models.ForeignKey('Invitation', on_delete=models.CASCADE, related_name='registered_users')
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    registration_date = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.full_name} ({self.email})"
    


class ExportJob(TimestampedModel):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    export_format = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file = models.FileField(upload_to='exports/', null=True, blank=True)
    progress = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Export {self.id} - {self.export_format} ({self.status})"