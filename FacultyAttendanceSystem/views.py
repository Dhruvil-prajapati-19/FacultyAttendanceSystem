from django.shortcuts import render,redirect
from .models import Faculty, Timetable,AdminCredentials
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages

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
    # Add your view logic here
    return render(request, 'index.html')  # Assuming you have an 'index.html' template

def timetable(request, faculty_id):
    faculty = Faculty.objects.get(pk=faculty_id)
    timetable_data = Timetable.objects.filter(faculty=faculty)
    return render(request, 'timetable.html', {'timetable_data': timetable_data})

