from django.shortcuts import render,redirect
from .models import AdminCredentials
from datetime import datetime, timedelta
from .models import TimeTableRollouts
from django.urls import reverse


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

        # Calculate the start date of the week (Monday) preceding the selected date
        start_date = selected_date - timedelta(days=selected_date.weekday())

        # Calculate the end date of the week (Sunday)
        end_date = start_date + timedelta(days=6)

        # Fetch class rollouts for the selected week
        class_rollouts = TimeTableRollouts.objects.filter(class_date__range=[start_date, end_date])

        # Pass the dates and class rollouts to the template
        return render(request, 'index.html', {
            'success': True,
            'selected_date': selected_date.strftime('%Y-%m-%d'),
            'monday_date': start_date.strftime('%d-%m-%Y'),
            'sunday_date': end_date.strftime('%d-%m-%Y'),
            'class_rollouts': class_rollouts,
        })

    return render(request, 'index.html', {'success': False})


def toggle_attendance(request, class_rollout_id):
    if request.method == 'POST':
        class_rollout = TimeTableRollouts.objects.get(pk=class_rollout_id)
        # Toggle the attendance status
        class_rollout.class_attendance = not class_rollout.class_attendance
        class_rollout.save()
        # Redirect back to the index page or wherever appropriate
        return redirect('index')



