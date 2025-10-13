from django.shortcuts import render

def home_page(request):
    context = {
        'active_menu': 'visitor_invitation',
        # Add data for stats, table data, etc., if dynamic
    }
    return render(request, 'home.html', context)