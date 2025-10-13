# events/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db.models import Sum
from .models import Event, TicketClass, Exhibitor, ExhibitorTicketAllocation, TeamMember
from .forms import EventForm, TicketClassForm, ExhibitorForm, ExhibitorTicketAllocationForm, TeamMemberForm
from django.forms import modelform_factory

@login_required
def event_list(request):
    events = Event.objects.all()
    return render(request, 'events/event_list.html', {'object_list': events})

@login_required
def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    return render(request, 'events/event_detail.html', {'object': event})

@login_required
def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, 'Event created successfully.')
            return redirect('events:event_list')
    else:
        form = EventForm()
    return render(request, 'events/event_form.html', {'form': form})

@login_required
def event_update(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully.')
            return redirect('events:event_list')
    else:
        form = EventForm(instance=event)
    return render(request, 'events/event_form.html', {'form': form})

@login_required
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully.')
        return redirect('events:event_list')
    return render(request, 'events/event_confirm_delete.html', {'object': event})

@login_required
def ticketclass_list(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    ticket_classes = TicketClass.objects.filter(event=event)
    return render(request, 'events/ticketclass_list.html', {'object_list': ticket_classes, 'event': event})

@login_required
def ticketclass_create(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if request.method == 'POST':
        form = TicketClassForm(request.POST)
        if form.is_valid():
            ticket_class = form.save(commit=False)
            ticket_class.event = event
            ticket_class.save()
            messages.success(request, 'Ticket class created successfully.')
            return redirect('events:ticketclass_list', event_id=event_id)
    else:
        form = TicketClassForm(initial={'event': event})
    return render(request, 'events/ticketclass_form.html', {'form': form, 'event': event})

@login_required
def ticketclass_update(request, pk, event_id):
    event = get_object_or_404(Event, pk=event_id)
    ticket_class = get_object_or_404(TicketClass, pk=pk, event=event)
    if request.method == 'POST':
        form = TicketClassForm(request.POST, instance=ticket_class)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ticket class updated successfully.')
            return redirect('events:ticketclass_list', event_id=event_id)
    else:
        form = TicketClassForm(instance=ticket_class)
    return render(request, 'events/ticketclass_form.html', {'form': form, 'event': event})

@login_required
def ticketclass_delete(request, pk, event_id):
    event = get_object_or_404(Event, pk=event_id)
    ticket_class = get_object_or_404(TicketClass, pk=pk, event=event)
    if request.method == 'POST':
        ticket_class.delete()
        messages.success(request, 'Ticket class deleted successfully.')
        return redirect('events:ticketclass_list', event_id=event_id)
    return render(request, 'events/ticketclass_confirm_delete.html', {'object': ticket_class, 'event': event})

@login_required
def exhibitor_list(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    exhibitors = Exhibitor.objects.filter(event=event)
    return render(request, 'events/exhibitor_list.html', {'object_list': exhibitors, 'event': event})

@login_required
def exhibitor_create(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if request.method == 'POST':
        form = ExhibitorForm(request.POST)
        if form.is_valid():
            exhibitor = form.save(commit=False)
            exhibitor.event = event
            exhibitor.save()
            messages.success(request, 'Exhibitor created successfully.')
            return redirect('events:exhibitor_list', event_id=event_id)
    else:
        form = ExhibitorForm(initial={'event': event})
    return render(request, 'events/exhibitor_form.html', {'form': form, 'event': event})

@login_required
def exhibitor_update(request, pk, event_id):
    event = get_object_or_404(Event, pk=event_id)
    exhibitor = get_object_or_404(Exhibitor, pk=pk, event=event)
    if request.method == 'POST':
        form = ExhibitorForm(request.POST, instance=exhibitor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exhibitor updated successfully.')
            return redirect('events:exhibitor_list', event_id=event_id)
    else:
        form = ExhibitorForm(instance=exhibitor)
    return render(request, 'events/exhibitor_form.html', {'form': form, 'event': event})

@login_required
def exhibitor_delete(request, pk, event_id):
    event = get_object_or_404(Event, pk=event_id)
    exhibitor = get_object_or_404(Exhibitor, pk=pk, event=event)
    if request.method == 'POST':
        exhibitor.delete()
        messages.success(request, 'Exhibitor deleted successfully.')
        return redirect('events:exhibitor_list', event_id=event_id)
    return render(request, 'events/exhibitor_confirm_delete.html', {'object': exhibitor, 'event': event})

@login_required
def ticket_allocation_list(request, event_id, exhibitor_id):
    event = get_object_or_404(Event, pk=event_id)
    exhibitor = get_object_or_404(Exhibitor, pk=exhibitor_id, event=event) 
    allocations = ExhibitorTicketAllocation.objects.filter(exhibitor=exhibitor)
    return render(request, 'events/exhibitor_ticket_allocation_list.html', {
        'object_list': allocations,
        'exhibitor': exhibitor,
        'event': event 
    })



@login_required
def ticket_allocation_create(request, exhibitor_id):
    exhibitor = get_object_or_404(Exhibitor, pk=exhibitor_id)
    event = exhibitor.event
    ticket_class_id = request.GET.get('ticket_class')
    if request.method == 'POST':
        form = ExhibitorTicketAllocationForm(request.POST)
        form.fields['ticket_class'].queryset = TicketClass.objects.filter(event=exhibitor.event)
        if form.is_valid():
            allocation = form.save(commit=False)
            allocation.exhibitor = exhibitor
            # Check for existing allocation
            exists = ExhibitorTicketAllocation.objects.filter(
                exhibitor=exhibitor,
                ticket_class=allocation.ticket_class
            ).exists()
            if exists:
                messages.error(request, 'An allocation for this ticket class already exists for this exhibitor.')
            else:
                allocation.save()
                messages.success(request, 'Ticket allocation created successfully.')
                return redirect('events:ticket_allocation_list', event_id=event.id, exhibitor_id=exhibitor_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ExhibitorTicketAllocationForm(initial={'exhibitor': exhibitor})
        form.fields['ticket_class'].queryset = TicketClass.objects.filter(event=exhibitor.event)
        if ticket_class_id:
            try:
                tc = TicketClass.objects.get(pk=ticket_class_id, event=exhibitor.event)
                form.initial['ticket_class'] = tc
            except TicketClass.DoesNotExist:
                pass
    return render(request, 'events/exhibitor_ticket_allocation_form.html', {'form': form, 'exhibitor': exhibitor, 'event': event})


@login_required
def ticket_allocation_update(request, pk, exhibitor_id):
    exhibitor = get_object_or_404(Exhibitor, pk=exhibitor_id)
    allocation = get_object_or_404(ExhibitorTicketAllocation, pk=pk, exhibitor=exhibitor)
    if request.method == 'POST':
        form = ExhibitorTicketAllocationForm(request.POST, instance=allocation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ticket allocation updated successfully.')
            return redirect('events:ticket_allocation_list', event_id=exhibitor.event.id, exhibitor_id=exhibitor_id)
    else:
        form = ExhibitorTicketAllocationForm(instance=allocation)
        form.fields['ticket_class'].queryset = TicketClass.objects.filter(event=exhibitor.event)
    return render(request, 'events/exhibitor_ticket_allocation_form.html', {'form': form, 'exhibitor': exhibitor})

@login_required
def ticket_allocation_delete(request, pk, exhibitor_id):
    exhibitor = get_object_or_404(Exhibitor, pk=exhibitor_id)
    allocation = get_object_or_404(ExhibitorTicketAllocation, pk=pk, exhibitor=exhibitor)
    if request.method == 'POST':
        allocation.delete()
        messages.success(request, 'Ticket allocation deleted successfully.')
        return redirect('events:ticket_allocation_list', exhibitor_id=exhibitor_id)
    return render(request, 'events/exhibitor_ticket_allocation_confirm_delete.html', {'object': allocation, 'exhibitor': exhibitor})

@login_required
def teammember_list(request, exhibitor_id):
    exhibitor = get_object_or_404(Exhibitor, pk=exhibitor_id)
    team_members = TeamMember.objects.filter(exhibitor=exhibitor)
    return render(request, 'events/teammember_list.html', {'object_list': team_members, 'exhibitor': exhibitor})

@login_required
def teammember_create(request, exhibitor_id):
    exhibitor = get_object_or_404(Exhibitor, pk=exhibitor_id)
    if request.method == 'POST':
        form = TeamMemberForm(request.POST)
        if form.is_valid():
            team_member = form.save(commit=False)
            team_member.exhibitor = exhibitor
            team_member.save()
            messages.success(request, 'Team member created successfully.')
            return redirect('events:teammember_list', exhibitor_id=exhibitor_id)
    else:
        form = TeamMemberForm(initial={'exhibitor': exhibitor, 'company_name': exhibitor.company_name})
    return render(request, 'events/teammember_form.html', {'form': form, 'exhibitor': exhibitor})

@login_required
def teammember_update(request, pk, exhibitor_id):
    exhibitor = get_object_or_404(Exhibitor, pk=exhibitor_id)
    team_member = get_object_or_404(TeamMember, pk=pk, exhibitor=exhibitor)
    if request.method == 'POST':
        form = TeamMemberForm(request.POST, instance=team_member)
        if form.is_valid():
            form.save()
            messages.success(request, 'Team member updated successfully.')
            return redirect('events:teammember_list', exhibitor_id=exhibitor_id)
    else:
        form = TeamMemberForm(instance=team_member)
    return render(request, 'events/teammember_form.html', {'form': form, 'exhibitor': exhibitor})

@login_required
def teammember_delete(request, pk, exhibitor_id):
    exhibitor = get_object_or_404(Exhibitor, pk=exhibitor_id)
    team_member = get_object_or_404(TeamMember, pk=pk, exhibitor=exhibitor)
    if request.method == 'POST':
        team_member.delete()
        messages.success(request, 'Team member deleted successfully.')
        return redirect('events:teammember_list', exhibitor_id=exhibitor_id)
    return render(request, 'events/teammember_confirm_delete.html', {'object': team_member, 'exhibitor': exhibitor})

