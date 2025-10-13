from django import forms

class FileUploadForm(forms.Form):
    file = forms.FileField(label='Select a file')

class InvitationForm(forms.Form):
    email = forms.EmailField(label='Invitee Email')
    message = forms.CharField(
        label='Message',
        widget=forms.Textarea,
        required=False
    )