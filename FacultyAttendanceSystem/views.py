from django.shortcuts import render,redirect
from .models import AdminCredentials
from datetime import datetime, timedelta
from .models import TimeTableRollouts
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from .models import AdminCredentials

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            # Fetch admin credentials based on the provided username
            admin_credentials = AdminCredentials.objects.get(username=username)
            
            if admin_credentials.password == password:
                messages.success(request, 'You have successfully logged in.')
                return redirect('index/')
            else:
                error_message = 'Invalid password'
        except AdminCredentials.DoesNotExist:
            error_message = 'Invalid username or password'
        
        # Display error message
        messages.error(request, error_message)
    
    return render(request, 'login.html')


def calendar(request):
    if request.method == 'GET':
        selected_date_str = request.GET.get('weekpicker', None)
        if selected_date_str:
            try:
                selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d')
            except ValueError:
                selected_date = datetime.now().date()  
        else:
            selected_date = datetime.now().date()  

        start_date = selected_date - timedelta(days=selected_date.weekday())
        end_date = start_date + timedelta(days=6)

        class_rollouts_by_day = {
            'Monday': TimeTableRollouts.objects.filter(class_date=start_date),
            'Tuesday': TimeTableRollouts.objects.filter(class_date=start_date + timedelta(days=1)),
            'Wednesday': TimeTableRollouts.objects.filter(class_date=start_date + timedelta(days=2)),
            'Thursday': TimeTableRollouts.objects.filter(class_date=start_date + timedelta(days=3)),
            'Friday': TimeTableRollouts.objects.filter(class_date=start_date + timedelta(days=4)),
            'Saturday': TimeTableRollouts.objects.filter(class_date=start_date + timedelta(days=5)),
            'Sunday': TimeTableRollouts.objects.filter(class_date=end_date),
        }

        additional_entries = {}
        for day, rollouts in class_rollouts_by_day.items():
            additional_entries[day] = [None] * max(0, 6 - rollouts.count())

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
            'class_rollouts_by_day': class_rollouts_by_day,
            'additional_entries': additional_entries,
        })

    return render(request, 'index.html', {'success': False})

def toggle_attendance(request, class_rollout_id):
    if request.method == 'POST':
        class_rollout = TimeTableRollouts.objects.get(pk=class_rollout_id)
        # Toggle the attendance status
        class_rollout.class_attedance = not class_rollout.class_attedance
        class_rollout.save()
        # Redirect back to the index page or wherever appropriate
        return redirect('index')



