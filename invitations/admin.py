from django.contrib import admin
from invitations.models import Invitation, InvitationCSVUpload, RegisteredUser

# Register your models here.
admin.site.register(Invitation)
admin.site.register(InvitationCSVUpload)
admin.site.register(RegisteredUser)