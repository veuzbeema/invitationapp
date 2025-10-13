# events/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Event, TicketClass, Exhibitor, ExhibitorTicketAllocation, TeamMember, TicketType
from accounts.models import User

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'description', 'start_date', 'end_date', 'location']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and end_date <= start_date:
            raise ValidationError('End date must be after start date.')
        return cleaned_data

class TicketClassForm(forms.ModelForm):
    class Meta:
        model = TicketClass
        fields = ['name', 'ticket_type', 'sale_start', 'sale_end', 'price', 'quantity_limit']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'ticket_type': forms.Select(attrs={'class': 'form-control'}),
            'sale_start': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'sale_end': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantity_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        if event:
            self.fields['event'].initial = event
            self.fields['event'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        sale_start = cleaned_data.get('sale_start')
        sale_end = cleaned_data.get('sale_end')
        if sale_start and sale_end and sale_end <= sale_start:
            raise ValidationError('Sale end must be after sale start.')
        return cleaned_data

class ExhibitorForm(forms.ModelForm):
    class Meta:
        model = Exhibitor
        fields = ['company_name', 'phone_number', 'booth']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'booth': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        if event:
            self.fields['event'].initial = event
            self.fields['event'].widget = forms.HiddenInput()


class ExhibitorTicketAllocationForm(forms.ModelForm):
    class Meta:
        model = ExhibitorTicketAllocation
        fields = ['ticket_class', 'quantity', 'is_paid']
        widgets = {
            'ticket_class': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        exhibitor = kwargs.pop('exhibitor', None)
        super().__init__(*args, **kwargs)
        if exhibitor:
            self.fields['exhibitor'].initial = exhibitor
            self.fields['exhibitor'].widget = forms.HiddenInput()
        self.fields['ticket_class'].queryset = TicketClass.objects.none()  # Will be set in view

    def clean(self):
        cleaned_data = super().clean()
        ticket_class = cleaned_data.get('ticket_class')
        exhibitor = cleaned_data.get('exhibitor')
        if ticket_class and exhibitor:
            if ExhibitorTicketAllocation.objects.filter(exhibitor=exhibitor, ticket_class=ticket_class).exists():
                raise ValidationError('Allocation already exists for this ticket class.')
        return cleaned_data


class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = ['name', 'email', 'phone_number', 'specialization', 'company_name', 'position',
                  'login_access', 'company_admin', 'lead_capture_access', 'lead_export_access']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.Select(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'login_access': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'company_admin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'lead_capture_access': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'lead_export_access': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


    def __init__(self, *args, **kwargs):
        exhibitor = kwargs.pop('exhibitor', None)
        super().__init__(*args, **kwargs)
        if exhibitor:
            self.fields['exhibitor'].initial = exhibitor
            self.fields['exhibitor'].widget = forms.HiddenInput()
        self.fields['name'].required = True
        self.fields['email'].required = True
        self.fields['specialization'].required = True
        self.fields['company_name'].required = True
        self.fields['phone_number'].required = False
        self.fields['position'].required = False


    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            user = None
            if self.instance and self.instance.user:
                user = self.instance.user
            if user:
                if User.objects.filter(username=username).exclude(pk=user.pk).exists():
                    raise ValidationError('Username already exists.')
            else:
                if User.objects.filter(username=username).exists():
                    raise ValidationError('Username already exists.')
        return username