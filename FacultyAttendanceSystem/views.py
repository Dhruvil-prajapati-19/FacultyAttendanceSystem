from django.shortcuts import render,redirect
from .models import AdminCredentials
from datetime import datetime, timedelta



def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Fetch admin credentials based on the provided username
        admin_credentials = AdminCredentials.objects.filter(username=username).first()
        
        if admin_credentials and admin_credentials.password == password:
            return redirect('index')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    else:
        return render(request, 'login.html')
 


def index(request):
    return render(request, 'index.html') 

def calendar(request):
    if request.method == 'GET':
        # Default to today's date if no date is selected
        selected_date_str = request.GET.get('weekpicker', None)
        if selected_date_str:
            try:
                selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d')
            except ValueError:
                selected_date = datetime.now().date()  
        else:
            selected_date = datetime.now().date()  # Default to today's date if no date is selected

        # Calculate start and end dates of the week
        start_date = selected_date - timedelta(days=selected_date.weekday())
        end_date = start_date + timedelta(days=6)

        # Pass the dates to the template
        return render(request, 'index.html', {
            'success': True,
            'selected_date': selected_date.strftime('%Y-%m-%d'),
            'monday_date': start_date.strftime('%Y-%m-%d'),
            'tuesday_date': (start_date + timedelta(days=1)).strftime('%d-%m-%Y'),
            'wednesday_date': (start_date + timedelta(days=2)).strftime('%d-%m-%Y'),
            'thursday_date': (start_date + timedelta(days=3)).strftime('%d-%m-%Y'),
            'friday_date': (start_date + timedelta(days=4)).strftime('%d-%m-%Y'),
            'saturday_date': (start_date + timedelta(days=5)).strftime('%d-%m-%Y'),
            'sunday_date': end_date.strftime('%Y-%m-%d'),
        })

    return render(request, 'index.html', {'success': False})



