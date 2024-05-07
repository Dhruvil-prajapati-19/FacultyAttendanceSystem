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

from django.shortcuts import render
from datetime import datetime, timedelta

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

        # Calculate the start date of the week (Monday) preceding the selected date
        start_date = selected_date - timedelta(days=selected_date.weekday())

        # Calculate the end date of the week (Sunday)
        end_date = start_date + timedelta(days=6)

        # Pass the dates to the template
        return render(request, 'index.html', {
            'success': True,
            'selected_date': selected_date.strftime('%Y-%m-%d'),
            'monday_date': start_date.strftime('%d-%m-%Y'),
            'tuesday_date': (start_date + timedelta(days=1)).strftime('%d-%m-%Y'),
            'wednesday_date': (start_date + timedelta(days=2)).strftime('%d-%m-%Y'),
            'thursday_date': (start_date + timedelta(days=3)).strftime('%d-%m-%Y'),
            'friday_date': (start_date + timedelta(days=4)).strftime('%d-%m-%Y'),
            'saturday_date': (start_date + timedelta(days=5)).strftime('%d-%m-%Y'),
            'sunday_date': end_date.strftime('%d-%m-%Y'),
        })

    return render(request, 'index.html', {'success': False})



