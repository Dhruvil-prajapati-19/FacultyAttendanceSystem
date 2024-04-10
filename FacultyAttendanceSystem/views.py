from django.shortcuts import render
from .models import Faculty, Timetable

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
    return render(request, 'login.html')

def timetable(request, faculty_id):
    faculty = Faculty.objects.get(pk=faculty_id)
    timetable_data = Timetable.objects.filter(faculty=faculty)
    return render(request, 'timetable.html', {'timetable_data': timetable_data})
