from django.contrib import admin

# Register your models here.
from .models import *


admin.site.register(ExhibitorTicketAllocation)
admin.site.register(Event)
admin.site.register(TicketClass)
admin.site.register(Exhibitor)
admin.site.register(TeamMember)