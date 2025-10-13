from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from .models import Invitation
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
import json
import json
from .forms import InvitationForm
from django import forms

# views.py (complete functional views)
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from .models import Invitation, InvitationCSVUpload
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
import json
from datetime import date
import csv
from io import StringIO
from events.models import Event, TicketClass
import uuid
from datetime import datetime
import re
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import ValidationError
import re

from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum
from .models import Invitation  , RegisteredUser, InvitationCSVUpload
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import datetime, date
import json
import re
import csv
from events.models import ExhibitorTicketAllocation
import logging

logger = logging.getLogger(__name__)

# Create your views here.
class FileUploadForm(forms.Form):
    file = forms.FileField()

@csrf_exempt
@require_http_methods(["POST", "GET"])
def file_upload_view(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            fs = FileSystemStorage()
            filename = fs.save(uploaded_file.name, uploaded_file)
            file_url = fs.url(filename)
            return render(request, 'invitations/file_upload_success.html', {'file_url': file_url})
    else:
        form = FileUploadForm()
    return render(request, 'invitations/file_upload_form.html', {'form': form})

# def invitation_list_view(request):
#     invitations = Invitation.objects.all()
#     return render(request, 'invitations/invitation_list.html', {'invitations': invitations})


# @login_required
@require_http_methods(["GET"])
def invitation_list_view(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # AJAX request for DataTables
        try:
            invitations = Invitation.objects.filter(event__created_by=request.user).order_by('-created_at')
            invitations_data = []
            for inv in invitations:
                invitations_data.append({
                    'name': inv.title_or_name or 'N/A',
                    'email': inv.email or 'N/A',
                    'type': inv.get_invite_type_display() or inv.invite_type,
                    'expiry': inv.expiry_date.strftime('%Y-%m-%d') if inv.expiry_date else 'N/A',
                    'limit': inv.link_limit or 0,
                    'registered': inv.registered_count or 0,
                    'status': inv.status.capitalize(),
                    'key': inv.invitation_key or ''
                })
            logger.debug(f"Returning {len(invitations_data)} invitations for DataTables")
            return JsonResponse({'data': invitations_data}, status=200)
        except Exception as e:
            logger.error(f"Error in invitation_list AJAX: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    try:
        # General ticket stats
        total_tickets = ExhibitorTicketAllocation.objects.filter(
            exhibitor__event__created_by=request.user
        ).aggregate(total=Sum('quantity'))['total'] or 0
        used_tickets = ExhibitorTicketAllocation.objects.filter(
            exhibitor__event__created_by=request.user, is_used=True
        ).aggregate(total=Sum('quantity'))['total'] or 0
        available_tickets = total_tickets - used_tickets

        # Ticket type stats for cards
        ticket_types = []
        ticket_classes = TicketClass.objects.filter(event__created_by=request.user)
        for ticket_class in ticket_classes:
            total = ExhibitorTicketAllocation.objects.filter(
                ticket_class=ticket_class,
                exhibitor__event__created_by=request.user
            ).aggregate(total=Sum('quantity'))['total'] or 0
            used = ExhibitorTicketAllocation.objects.filter(
                ticket_class=ticket_class,
                exhibitor__event__created_by=request.user,
                is_used=True
            ).aggregate(total=Sum('quantity'))['total'] or 0
            ticket_types.append({
                'name': ticket_class.ticket_type,  # Adjust to ticket_class.name if needed
                'used': used,
                'total': total,
                'color_class': {
                    'visitor': 'info',
                    'vip': 'success',
                    'gold': 'warning',
                    'platinum': 'primary',
                    'exhibitor': 'secondary'
                }.get(ticket_class.ticket_type.lower(), 'primary')
            })

        # Additional stats for other cards
        generated_invitations = Invitation.objects.filter(event__created_by=request.user).count()
        registered_visitors = Invitation.objects.filter(
            event__created_by=request.user
        ).aggregate(total=Sum('registered_count'))['total'] or 0

        context = {
            'today': date.today(),
            'total_tickets': total_tickets,
            'used_tickets': used_tickets,
            'available_tickets': available_tickets,
            'allocated_invitations': total_tickets,
            'generated_invitations': generated_invitations,
            'registered_visitors': registered_visitors,
            'ticket_types': ticket_types,
        }
        return render(request, 'invitations/invitation_list.html', context)
    except Exception as e:
        logger.error(f"Error rendering invitation_list: {str(e)}")
        return render(request, 'invitations/invitation_list.html', {'error': str(e)})



def invitation_create_view(request):
    if request.method == 'POST':
        form = InvitationForm(request.POST, request.FILES)
        if form.is_valid():
            invitation = form.save()
            return render(request, 'invitations/invitation_detail.html', {'invitation': invitation})
    else:
        form = InvitationForm()
    return render(request, 'invitations/invitation_form.html', {'form': form})

def invitation_update_view(request, invitation_id):
    try:
        invitation = Invitation.objects.get(id=invitation_id)
    except Invitation.DoesNotExist:
        return render(request, 'invitations/not_found.html', status=404)
    if request.method == 'POST':
        form = InvitationForm(request.POST, request.FILES, instance=invitation)
        if form.is_valid():
            invitation = form.save()
            return render(request, 'invitations/invitation_detail.html', {'invitation': invitation})
    else:
        form = InvitationForm(instance=invitation)
    return render(request, 'invitations/invitation_form.html', {'form': form, 'invitation': invitation})

def invitation_delete_view(request, invitation_id):
    try:
        invitation = Invitation.objects.get(id=invitation_id)
    except Invitation.DoesNotExist:
        return render(request, 'invitations/not_found.html', status=404)
    if request.method == 'POST':
        invitation.delete()
        return render(request, 'invitations/invitation_deleted.html')
    return render(request, 'invitations/invitation_confirm_delete.html', {'invitation': invitation})





def validate_email(email):
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(pattern, email) is not None

@csrf_exempt
@require_http_methods(["POST"])
def send_personalized_invitation(request):
    """
    Handle sending a single personalized invitation via AJAX POST.
    """
    try:
        data = json.loads(request.body)
        guest_name = data.get('guestName')
        guest_email = data.get('guestEmail')
        ticket_type = data.get('ticketType')
        company_name = data.get('companyName', '')
        personal_message = data.get('personalMessage', '')
        expire_date_str = data.get('personalExpireDate')
        
        if not all([guest_name, guest_email, ticket_type, expire_date_str]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
        
        if not validate_email(guest_email):
            return JsonResponse({'success': False, 'error': 'Invalid email'}, status=400)
        
        # Parse expire date
        expire_date = datetime.strptime(expire_date_str, '%Y-%m-%d').replace(tzinfo=None)
        
        # Get event and ticket class (assuming first event for demo; adjust to user's event)
        event = Event.objects.first()
        if not event:
            return JsonResponse({'success': False, 'error': 'No event found'}, status=500)
        
        try:
            ticket_class = TicketClass.objects.get(event=event,ticket_type=ticket_type)
        except TicketClass.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'Invalid ticket type: {ticket_type}'}, status=400)
        
        # Generate invitation key
        invitation_key = str(uuid.uuid4()).replace('-', '')[:12].upper()
        
        # Create invitation
        invitation = Invitation.objects.create(
            event=event,
            title_or_name=guest_name,
            email=guest_email,
            invite_type='personalized',
            expiry_date=expire_date,
            link_limit=1,
            invitation_key=invitation_key,
            status='active',
            ticket_class=ticket_class,
            company_name=company_name,
            personal_message=personal_message,
        )
        
        # Send email
        subject = f'Invitation to GITEX GLOBAL 2025 - {ticket_type.upper()} Pass'
        message_body = f"""
        Dear {guest_name},

        {personal_message or 'We are pleased to invite you to GITEX GLOBAL 2025.'}

        Please register using this link: https://gitex.com/invite/{invitation_key}

        This invitation expires on: {expire_date_str}
        Company: {company_name or 'N/A'}

        Best regards,
        GITEX Team
                
                
        """
        sent = send_mail(
            subject,
            message_body,
            settings.DEFAULT_FROM_EMAIL,
            [guest_email],
            fail_silently=False,
        )
        # sent = True
        
        if sent:
            return JsonResponse({
                'success': True,
                'message': f'Invitation sent to {guest_email}',
                'invitation_id': invitation.id,
                'link': f'https://gitex.com/invite/{invitation_key}'
            })
        else:
            return JsonResponse({'success': False, 'error': 'Failed to send email'}, status=500)
            
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Invalid date format'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def send_bulk_personalized_invitation(request):
    """
    Handle bulk personalized invitations via AJAX POST with file upload.
    Parses CSV, saves to Invitation model, stores CSV in InvitationCSVUpload, sends emails.
    """
    try:
        # Get form data
        csv_file = request.FILES.get('bulkCsvFile')
        default_message = request.POST.get('bulkPersonalMessage', '')
        expire_date_str = request.POST.get('bulkExpireDate')
        
        if not csv_file or not expire_date_str:
            return JsonResponse({'success': False, 'error': 'Missing CSV file or expire date'}, status=400)
        
        # Parse expire date
        expire_date = datetime.strptime(expire_date_str, '%Y-%m-%d').replace(tzinfo=None)
        
        # Get event
        event = Event.objects.first()
        if not event:
            return JsonResponse({'success': False, 'error': 'No event found'}, status=500)
        
        # Read and parse CSV
        csv_data = csv_file.read().decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_data))
        
        # Validate headers (optional, but good practice)
        expected_headers = ['Full Name', 'Email', 'Ticket Type', 'Company Name', 'Personal Message']
        if not all(header in csv_reader.fieldnames for header in expected_headers[:3]):  # Required
            return JsonResponse({'success': False, 'error': 'Invalid CSV headers. Expected: Full Name, Email, Ticket Type'}, status=400)
        
        valid_ticket_types = ['visitor', 'vip', 'gold', 'platinum', 'exhibitor']
        valid_rows = 0
        errors = []
        created_invitations = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            name = row.get('Full Name', '').strip()
            email = row.get('Email', '').strip()
            ticket_type = row.get('Ticket Type', '').strip().lower()
            company = row.get('Company Name', '').strip()
            # personal_message = row.get('Personal Message', '').strip() or default_message
            personal_message = default_message


            print('----------------row-----------------', row)
            if not (name and email and ticket_type):
                errors.append(f'Row {row_num}: Missing required fields (Full Name, Email, Ticket Type)')
                continue
            
            if not validate_email(email):
                errors.append(f'Row {row_num}: Invalid email "{email}"')
                continue
            
            if ticket_type not in valid_ticket_types:
                errors.append(f'Row {row_num}: Invalid ticket type "{ticket_type}". Must be one of {valid_ticket_types}')
                continue
            
            try:
                ticket_class = TicketClass.objects.get(event=event,ticket_type=ticket_type)
            except TicketClass.DoesNotExist:
                errors.append(f'Row {row_num}: Ticket class "{ticket_type}" not found')
                continue
            
            # Generate key
            invitation_key = str(uuid.uuid4()).replace('-', '')[:12].upper()
            
            # Create invitation

            print('----------------invitation-----------------', name, email)
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
            created_invitations.append(invitation.id)
            
            # Send email (async in production, but sync here)
            subject = f'Bulk Invitation to GITEX GLOBAL 2025 - {ticket_type.upper()} Pass'
            message_body = f"""
                    Dear {name},

                    {personal_message}

                    Please register using this link: https://gitex.com/invite/{invitation_key}

                    This invitation expires on: {expire_date_str}
                    Company: {company or 'N/A'}

                    Best regards,
                    GITEX Team
            """
            # try:
            #     send_mail(
            #         subject,
            #         message_body,
            #         settings.DEFAULT_FROM_EMAIL,
            #         [email],
            #         fail_silently=True,
            #     )
            #     valid_rows += 1
            # except Exception as email_err:
            #     errors.append(f'Row {row_num}: Failed to send email - {str(email_err)}')
        
        # Store CSV file
        fs = FileSystemStorage()
        filename = fs.save(f'bulk_invitation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv', csv_file)
        file_path = fs.path(filename)
        
        # Create CSV upload record
        csv_upload = InvitationCSVUpload.objects.create(
            event=event,
            file=file_path,  # Full path or use save to field
            status='success' if not errors else 'failed' if valid_rows == 0 else 'processing',
            processed=True,
            processed_at=datetime.now(),
            processed_count=valid_rows,
            failed_count=len(errors),
            error_message='\n'.join(errors) if errors else ''
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully processed {valid_rows} invitations. Errors: {len(errors)}',
            'valid_count': valid_rows,
            'error_count': len(errors),
            'errors': errors[:10],  # First 10 errors
            'csv_upload_id': csv_upload.id,
            'created_invitations': created_invitations
        })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



@login_required
@require_http_methods(["GET"])
def invitation_list(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # AJAX request for DataTables
        try:
            # Fetch invitations for the logged-in user
            invitations = Invitation.objects.filter(event__created_by=request.user).order_by('-created_at')
            invitations_data = []

            for inv in invitations:
                invitations_data.append({
                    'name': inv.title_or_name or 'N/A',
                    'email': inv.email or 'N/A',
                    'type': inv.get_invite_type_display() or inv.invite_type,  # Use display for choices
                    'expiry': inv.expiry_date.strftime('%Y-%m-%d') if inv.expiry_date else 'N/A',
                    'limit': inv.link_limit or 0,
                    'registered': inv.registered_count or 0,
                    'status': inv.status.capitalize(),
                    'key': inv.invitation_key or ''
                })

            logger.debug(f"Returning {len(invitations_data)} invitations for DataTables")
            return JsonResponse({'data': invitations_data}, status=200)
        except Exception as e:
            logger.error(f"Error in invitation_list AJAX: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    try:
        total_tickets = ExhibitorTicketAllocation.objects.filter(
            exhibitor__event__created_by=request.user
        ).aggregate(total=Sum('quantity'))['total'] or 0
        used_tickets = ExhibitorTicketAllocation.objects.filter(
            exhibitor__event__created_by=request.user, is_used=True
        ).aggregate(total=Sum('quantity'))['total'] or 0
        available_tickets = total_tickets - used_tickets

        ticket_types = []
        ticket_classes = TicketClass.objects.filter(event__created_by=request.user)
        for ticket_class in ticket_classes:
            total = ExhibitorTicketAllocation.objects.filter(
                ticket_class=ticket_class,
                exhibitor__event__created_by=request.user
            ).aggregate(total=Sum('quantity'))['total'] or 0
            used = ExhibitorTicketAllocation.objects.filter(
                ticket_class=ticket_class,
                exhibitor__event__created_by=request.user,
                is_used=True
            ).aggregate(total=Sum('quantity'))['total'] or 0
            ticket_types.append({
                'name': ticket_class.ticket_type,  # Use ticket_type (Enum or field)
                'used': used,
                'total': total,
                'color_class': {
                    'visitor': 'info',
                    'vip': 'success',
                    'gold': 'warning',
                    'platinum': 'primary',
                    'exhibitor': 'secondary'
                }.get(ticket_class.ticket_type.lower(), 'primary')
            })

        context = {
            'total_tickets': total_tickets,
            'used_tickets': used_tickets,
            'available_tickets': available_tickets,
            'allocated_invitations': 345, 
            'generated_invitations': 120, 
            'remaining_invitations': 500,
            'registered_visitors': int(20),
            'ticket_types': ticket_types,
        }
        return render(request, 'invitations/invitation_list.html', context)
    except Exception as e:
        logger.error(f"Error rendering invitation_list: {str(e)}")
        return render(request, 'invitations/invitation_list.html', {'error': str(e)})
    


@csrf_exempt
@require_http_methods(["POST"])
def edit_invitation(request):
    """
    Edit an existing invitation via AJAX POST.
    """
    try:
        data = json.loads(request.body)
        invitation_id = data.get('invitationId')
        title_or_name = data.get('guestName')
        ticket_type = data.get('ticketType')
        company_name = data.get('companyName')
        personal_message = data.get('personalMessage')
        expire_date_str = data.get('expireDate')
        link_limit = int(data.get('linkLimit', 1))
        status = data.get('status')

        if not all([invitation_id, title_or_name, ticket_type, expire_date_str, link_limit, status]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)

        if link_limit > 100:
            return JsonResponse({'success': False, 'error': 'Link limit exceeds maximum (100)'}, status=400)

        try:
            invitation = Invitation.objects.get(id=invitation_id)
        except Invitation.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invitation not found'}, status=404)

        event = Event.objects.first()
        if not event:
            return JsonResponse({'success': False, 'error': 'No event found'}, status=500)

        try:
            ticket_class = TicketClass.objects.get(event=event, ticket_type=ticket_type)
        except TicketClass.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'Invalid ticket type: {ticket_type}'}, status=400)

        try:
            expire_date = datetime.strptime(expire_date_str, '%Y-%m-%d').replace(tzinfo=None)
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid date format'}, status=400)

        # Update invitation fields
        invitation.title_or_name = title_or_name
        invitation.ticket_class = ticket_class
        invitation.company_name = company_name
        invitation.personal_message = personal_message
        invitation.expiry_date = expire_date
        invitation.link_limit = link_limit
        invitation.status = status
        invitation.save()

        return JsonResponse({
            'success': True,
            'message': f'Invitation {title_or_name} updated successfully'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
@require_http_methods(["GET", "POST"])
def invitation_register_view(request, invitation_key):
    try:
        invitation = Invitation.objects.get(invitation_key=invitation_key, status='active')
    except Invitation.DoesNotExist:
        return render(request, 'invitations/invitation_invalid.html', status=404)

    if invitation.expiry_date and invitation.expiry_date < date.today():
        return render(request, 'invitations/invitation_expired.html', {'invitation': invitation})

    if request.method == 'POST':
        # Example: Register the user (you can expand this logic as needed)
        invitation.registered_count = (invitation.registered_count or 0) + 1
        invitation.save()
        return render(request, 'invitations/invitation_registered.html', {'invitation': invitation})

    return render(request, 'invitations/invitation_register.html', {'invitation': invitation})


def invite_landing(request, invitation_key):
    # Validate invitation key
    invitation = get_object_or_404(Invitation, invitation_key=invitation_key)
    
    # Check if invitation is active and not expired
    if invitation.status != 'active' or invitation.expiry_date < timezone.now():
        return render(request, 'invitations/invite_landing.html', {
            'error': 'This invitation is either inactive or has expired.',
            'invitation_key': invitation_key,
            'event_name': invitation.event.name if invitation.event else 'GITEX GLOBAL 2025'
        })

    # Check link limit
    if invitation.registered_count >= invitation.link_limit:
        return render(request, 'invite_landing.html', {
            'error': 'This invitation has reached its registration limit.',
            'invitation_key': invitation_key,
            'event_name': invitation.event.name if invitation.event else 'GITEX GLOBAL 2025'
        })

    # Handle register button click (POST request from landing page)
    if request.method == 'POST':
        return redirect('invitations:invite_register', invitation_key=invitation_key)

    return render(request, 'invitations/invite_landing.html', {
        'invitation_key': invitation_key,
        'event_name': invitation.event.name if invitation.event else 'GITEX GLOBAL 2025',
        'title_or_name': invitation.title_or_name,
        'personal_message': invitation.personal_message
    })


@csrf_exempt
@require_http_methods(["GET", "POST"])
def invite_register(request, invitation_key):
    if request.method == 'GET':
        # Validate invitation key
        invitation = get_object_or_404(Invitation, invitation_key=invitation_key)
        
        # Check if invitation is active and not expired
        if invitation.status != 'active' or invitation.expiry_date < timezone.now():
            return render(request, 'invite_register.html', {
                'error': 'This invitation is either inactive or has expired.',
                'invitation_key': invitation_key
            })

        # Check link limit
        if invitation.registered_count >= invitation.link_limit:
            return render(request, 'invite_register.html', {
                'error': 'This invitation has reached its registration limit.',
                'invitation_key': invitation_key
            })

        return render(request, 'invitations/invite_register.html', {
            'invitation_key': invitation_key,
            'event_name': invitation.event.name if invitation.event else 'GITEX GLOBAL 2025'
        })

    elif request.method == 'POST':
        # Validate invitation
        invitation = get_object_or_404(Invitation, invitation_key=invitation_key)
        
        if invitation.status != 'active':
            return JsonResponse({'error': 'This invitation is not active.'}, status=400)
        
        if invitation.expiry_date < timezone.now():
            return JsonResponse({'error': 'This invitation has expired.'}, status=400)
        
        if invitation.registered_count >= invitation.link_limit:
            return JsonResponse({'error': 'This invitation has reached its registration limit.'}, status=400)

        # Extract form data
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()

        # Validate inputs
        if not full_name:
            return JsonResponse({'error': 'Full name is required.'}, status=400)
        
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not email or not re.match(email_regex, email):
            return JsonResponse({'error': 'A valid email address is required.'}, status=400)
        
        phone_regex = r'^\+?\d{8,15}$'
        if not phone or not re.match(phone_regex, phone):
            return JsonResponse({'error': 'A valid phone number is required.'}, status=400)

        # Check for duplicate email
        if RegisteredUser.objects.filter(email=email).exists():
            return JsonResponse({'error': 'This email is already registered.'}, status=400)

        try:
            # Create RegisteredUser
            registered_user = RegisteredUser.objects.create(
                invitation=invitation,
                full_name=full_name,
                email=email,
                phone=phone
            )

            # Increment registered_count
            invitation.registered_count += 1
            invitation.save()

            return JsonResponse({
                'message': 'Registration successful! Your visitor pass has been registered.',
                'full_name': full_name
            })

        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)

    else:
        return JsonResponse({'error': 'Method not allowed.'}, status=405)