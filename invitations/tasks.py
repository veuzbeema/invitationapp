from celery import shared_task
import csv
import uuid
from io import StringIO
from django.core.validators import validate_email as django_validate_email
from django.core.exceptions import ValidationError

from django.db.models import Q

from django.conf import settings
from django.core.mail import send_mail
from invitations.models import Invitation, InvitationCSVUpload, ExportJob


from .utils import export_csv, export_excel, export_pdf

@shared_task
def send_invitation_email(invitation_id):
    try:
        invitation = Invitation.objects.get(id=invitation_id)
    except Invitation.DoesNotExist:
        return 
    
    from django.conf import settings
    base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    registration_link = f'{base_url}/register/{invitation.invitation_key}/'
    
     
    # Send email (async in production, but sync here)
    subject = f'Bulk Invitation to GITEX GLOBAL 2025 - {invitation.ticket_class.ticket_type.upper()} Pass'
    message_body = f"""
    Dear {invitation.title_or_name},

    {invitation.personal_message or 'You are invited to attend GITEX GLOBAL 2025.'}

    Please register using this link: https://gitex.com/invite/{invitation.invitation_key}

    This invitation expires on: {invitation.expiry_date.strftime('%Y-%m-%d %H:%M:%S')}
    Company: {invitation.company_name or 'N/A'}

    Best regards,
    GITEX Team
    """

    send_mail(
        subject,
        message_body,
        settings.DEFAULT_FROM_EMAIL,
        [invitation.email],
        fail_silently=True,
    )


@shared_task
def send_bulk_invitations(csv_upload_id, expire_date_str, default_message):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f'Starting bulk invitation processing for CSV upload ID {csv_upload_id}')
    from events.models import TicketClass
    from django.core.validators import ValidationError
    from datetime import datetime
    from django.utils import timezone
    
    errors = []
    created_invitations = []
    valid_rows = 0
    
    try:
        invite_upload = InvitationCSVUpload.objects.get(id=csv_upload_id)
        csv_file = invite_upload.file
        event = invite_upload.event
        expire_date = datetime.strptime(expire_date_str, '%Y-%m-%d').replace(tzinfo=timezone.get_current_timezone())
        default_message = default_message or 'You are invited to attend GITEX GLOBAL 2025.'
        valid_ticket_types = set(TicketClass.objects.filter(event=event).values_list('ticket_type', flat=True))
        
        # Read and parse CSV
        csv_file.seek(0)
        csv_data = csv_file.read().decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_data))
        
        expected_headers = ['Full Name', 'Email', 'Ticket Type', 'Company Name', 'Personal Message']
        if not all(header in csv_reader.fieldnames for header in expected_headers[:3]):
            errors.append('Invalid CSV headers. Expected: Full Name, Email, Ticket Type')
            invite_upload.status = 'failed'
            invite_upload.error_log = '\n'.join(errors)
            invite_upload.processed = True
            invite_upload.save()
            return
        
        # Collect all emails to check for duplicates
        emails = []
        for row in csv_reader:
            email = row.get('Email', '').strip().lower()
            if email:
                emails.append(email)
        
        # Check duplicates within CSV and in database
        email_counts = {}
        for email in emails:
            email_counts[email] = email_counts.get(email, 0) + 1
        csv_duplicates = [email for email, count in email_counts.items() if count > 1]
        if csv_duplicates:
            errors.append(f'Warning: Duplicate emails in CSV: {", ".join(csv_duplicates[:5])}{"..." if len(csv_duplicates) > 5 else ""}')
        
        existing_invitations = Invitation.objects.filter(
            event=event,
            email__in=emails
        ).values_list('email', flat=True)
        existing_emails = set(existing_invitations)
        if existing_emails:
            errors.append(f'Warning: Emails already in database: {", ".join(list(existing_emails)[:5])}{"..." if len(existing_emails) > 5 else ""}')
        
        # Reset reader for processing
        csv_file.seek(0)
        csv_data = csv_file.read().decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_data))
        
        for row_num, row in enumerate(csv_reader, start=2):
            name = row.get('Full Name', '').strip()
            email = row.get('Email', '').strip().lower()
            ticket_type = row.get('Ticket Type', '').strip().lower()
            company = row.get('Company Name', '').strip()
            personal_message = row.get('Personal Message', default_message).strip()
            
            if not (name and email and ticket_type):
                errors.append(f'Row {row_num}: Missing required fields (Full Name, Email, Ticket Type)')
                continue
            
            try:
                django_validate_email(email)
            except ValidationError:
                errors.append(f'Row {row_num}: Invalid email "{email}"')
                continue
            
            if ticket_type not in valid_ticket_types:
                errors.append(f'Row {row_num}: Invalid ticket type "{ticket_type}". Must be one of {valid_ticket_types}')
                continue
            
            if email in csv_duplicates or email in existing_emails:
                errors.append(f'Row {row_num}: Skipping duplicate email "{email}"')
                continue
            
            try:
                ticket_class = TicketClass.objects.get(event=event, ticket_type=ticket_type)
            except TicketClass.DoesNotExist:
                errors.append(f'Row {row_num}: Ticket class "{ticket_type}" not found')
                continue
            
            invitation_key = str(uuid.uuid4()).replace('-', '')[:12].upper()
            
            invitation = Invitation.objects.create(
                event=event,
                title_or_name=name,
                email=email,
                invite_type='personalized',
                expiry_date=expire_date,
                link_limit=1,
                link_count=1,
                registered_count=0,
                invitation_key=invitation_key,
                status='active',
                ticket_class=ticket_class,
                company_name=company,
                personal_message=personal_message,
            )
            
            created_invitations.append(invitation.id)
            valid_rows += 1
            
            send_invitation_email.delay(invitation.id)
        
        # Update the upload record
        invite_upload.processed = True
        invite_upload.status = 'success' if not errors else ('partial' if valid_rows > 0 else 'failed')
        invite_upload.processed_count = valid_rows
        invite_upload.failed_count = len(errors)
        invite_upload.error_log = '\n'.join(errors)
        invite_upload.processed_at = timezone.now()
        invite_upload.save()
        
    except Exception as e:
        errors.append(f'Unexpected error: {str(e)}')
        invite_upload.processed = True
        invite_upload.status = 'failed'
        invite_upload.error_log = '\n'.join(errors)
        invite_upload.processed_at = timezone.now()
        invite_upload.save()
        raise
    logger.info(f'Completed processing: {valid_rows} valid rows, {len(errors)} errors: {errors}')
         



@shared_task(bind=True)
def export_invitations_task(self, export_format):
    from django.utils import timezone
    # Create export job record

    # keyword, status, inv_type, date_filter, export_format, user_id


    keyword = None
    status = None
    inv_type = None
    date_filter = None
    #export_format = None


    export_job = ExportJob.objects.create(
        export_format=export_format,
        status='processing',
        progress=0
    )
    
    try:
        # Get filtered invitations
        invitations = Invitation.objects.all()
        total_invitations = invitations.count()
        
        # Apply filters
        if keyword:
            invitations = invitations.filter(
                Q(guest_name__icontains=keyword) | 
                Q(guest_email__icontains=keyword) |
                Q(link_title__icontains=keyword)
            )
        if status:
            invitations = invitations.filter(status=status)
        if inv_type:
            if inv_type == 'link':
                invitations = invitations.filter(invitation_type='link')
            elif inv_type == 'personal':
                invitations = invitations.filter(invitation_type='personal')
        if date_filter:
            invitations = invitations.filter(expiry_date=date_filter)
        
        # Update progress after filtering
        export_job.progress = 20
        export_job.save()
        
        # Generate file based on format
        if export_format == 'csv':
            output = export_csv(invitations, export_job, total_invitations)
        elif export_format == 'excel':
            output = export_excel(invitations, export_job, total_invitations)
        elif export_format == 'pdf':
            output = export_pdf(invitations, export_job, total_invitations)
        else:
            raise ValueError('Invalid format')
        
        # Update job status
        export_job.status = 'completed'
        export_job.progress = 100
        export_job.file.save(
            f"invitations_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{export_format}",
            output
        )
        export_job.save()
        
        return {'job_id': export_job.id, 'status': 'completed'}
    
    except Exception as e:
        export_job.status = 'failed'
        export_job.error_message = str(e)
        export_job.progress = 0
        export_job.save()
        raise
