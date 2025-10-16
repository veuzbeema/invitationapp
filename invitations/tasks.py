from celery import shared_task
import csv
import uuid
from io import StringIO
from django.core.validators import validate_email as django_validate_email
from django.core.exceptions import ValidationError

from django.conf import settings
from django.core.mail import send_mail
from invitations.models import Invitation, InvitationCSVUpload




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
    from events.models import TicketClass  # adjust import if needed
    errors = []
    created_invitations = []
    valid_rows = 0

 
    invite_upload = InvitationCSVUpload.objects.get(id=csv_upload_id)

    csv_file = invite_upload.file
    event = invite_upload.event
    expire_date = expire_date_str
    default_message = default_message or 'You are invited to attend GITEX GLOBAL 2025.'
    valid_ticket_types = set(TicketClass.objects.filter(event=event).values_list('ticket_type', flat=True))

    # Read and parse CSV
    csv_data = csv_file.read().decode('utf-8')
    csv_reader = csv.DictReader(StringIO(csv_data))

    expected_headers = ['Full Name', 'Email', 'Ticket Type', 'Company Name', 'Personal Message']

    if not all(header in csv_reader.fieldnames for header in expected_headers[:3]):  # Required
        return True

    def validate_email(email):
        try:
            django_validate_email(email)
            return True
        except ValidationError:
            return False

    for row_num, row in enumerate(csv_reader, start=2):
        name = row.get('Full Name', '').strip()
        email = row.get('Email', '').strip()
        ticket_type = row.get('Ticket Type', '').strip().lower()
        company = row.get('Company Name', '').strip()
        personal_message = default_message

        if not (name and email and ticket_type):
            errors.append(f'Row {row_num}: Missing required fields (Full Name, Email, Ticket Type)')
            continue

        # if not validate_email(email):
        #     errors.append(f'Row {row_num}: Invalid email "{email}"')
        #     continue

        if ticket_type not in valid_ticket_types:
            errors.append(f'Row {row_num}: Invalid ticket type "{ticket_type}". Must be one of {valid_ticket_types}')
            continue

        try:
            ticket_class = TicketClass.objects.get(event=event, ticket_type=ticket_type)
        except TicketClass.DoesNotExist:
            errors.append(f'Row {row_num}: Ticket class "{ticket_type}" not found')
            continue

        invitation_key = str(uuid.uuid4()).replace('-', '')[:12].upper()


        if Invitation.objects.filter(email=email).exists():
            continue

        invitation = Invitation.objects.create(
            event=event,
            title_or_name=name,
            email=email,
            invite_type='personalized',
            expiry_date=expire_date,
            link_limit=1,
            invitation_key=invitation_key,
            status='active',
            ticket_class=ticket_class,
            company_name=company,
            personal_message=personal_message,
        )
        print(invitation.status, "===========status================")
        created_invitations.append(invitation.id)
        valid_rows += 1  

        send_invitation_email.delay(invitation.id)


    # Optionally, update the upload record with results/errors
    invite_upload.processed = True
    invite_upload.status = 'success' if not errors else 'failed'
    invite_upload.processed_count = len(created_invitations)
    invite_upload.failed_count = len(errors)
    invite_upload.error_log = '\n'.join(errors)
    invite_upload.save()
         

from io import BytesIO
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.core.files.base import ContentFile
from datetime import datetime
import os

@shared_task
def export_invitations_task(format, keyword, status, type, date):
    try:
        # Filter invitations based on provided parameters
        invitations = Invitation.objects.all()
        if keyword:
            invitations = invitations.filter(title_or_name__icontains=keyword) | invitations.filter(email__icontains=keyword)
        if status:
            invitations = status.lower()
        if type:
            invitations = invitations.filter(invite_type=type)
        if date:
            invitations = invitations.filter(expiry_date=date)

        # Generate file based on format
        file_name = f"invitations_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        file_path = os.path.join(settings.MEDIA_ROOT, 'exports', file_name)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if format == 'csv':
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['ID', 'Name', 'Email', 'Type', 'Expiry Date', 'Limit', 'Registered', 'Status', 'Key'])
            for inv in invitations:
                writer.writerow([
                    inv.id,
                    inv.title_or_name or 'N/A',
                    inv.email or 'N/A',
                    inv.invite_type,
                    inv.expiry_date.strftime('%Y-%m-%d') if inv.expiry_date else 'N/A',
                    inv.link_limit or 0,
                    inv.registered_count or 0,
                    inv.status.capitalize(),
                    inv.invitation_key or ''
                ])
            file_content = ContentFile(output.getvalue().encode('utf-8'))
            output.close()

        elif format == 'excel':
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = 'Invitations'
            ws.append(['ID', 'Name', 'Email', 'Type', 'Expiry Date', 'Limit', 'Registered', 'Status', 'Key'])
            for inv in invitations:
                ws.append([
                    inv.id,
                    inv.title_or_name or 'N/A',
                    inv.email or 'N/A',
                    inv.invite_type,
                    inv.expiry_date.strftime('%Y-%m-%d') if inv.expiry_date else 'N/A',
                    inv.link_limit or 0,
                    inv.registered_count or 0,
                    inv.status.capitalize(),
                    inv.invitation_key or ''
                ])
            output = BytesIO()
            wb.save(output)
            file_content = ContentFile(output.getvalue())
            output.close()

        elif format == 'pdf':
            output = BytesIO()
            c = canvas.Canvas(output, pagesize=letter)
            c.setFont('Helvetica', 12)
            c.drawString(50, 750, 'Invitations Export')
            y = 730
            for inv in invitations:
                if y < 50:
                    c.showPage()
                    y = 750
                c.drawString(50, y, f"ID: {inv.id}, Name: {inv.title_or_name or 'N/A'}, Email: {inv.email or 'N/A'}, Type: {inv.invite_type}, Status: {inv.status.capitalize()}")
                y -= 20
            c.save()
            file_content = ContentFile(output.getvalue())
            output.close()

        # Save file to media directory
        with open(file_path, 'wb') as f:
            f.write(file_content.read())
        
        # Return file URL
        file_url = f"{settings.MEDIA_URL}exports/{file_name}"
        return {'status': 'SUCCESS', 'file_url': file_url}

    except Exception as e:
        return {'status': 'FAILURE', 'error': str(e)}
