# mixing.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import AdminCredentials, Students
from django.db import IntegrityError
from django.utils import timezone
from django.db import IntegrityError
from geopy.distance import geodesic # type: ignore


class FacultyLoginMixin:
    def handle_faculty_login(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        if username and password:
            try:
                admin_credentials = AdminCredentials.objects.get(username=username)
                if admin_credentials.password == password:
                    request.session['logged_user'] = admin_credentials.faculty.id
                    return redirect('index/')
                else:
                    messages.error(request, 'Invalid password')
            except AdminCredentials.DoesNotExist:
                messages.error(request, 'Invalid username or password')
        return render(request, 'login.html', {'error_message': 'Invalid credentials'})

ALLOWED_LOCATION = (23.58729073245821, 72.38227230632735) # 23.85947073496859, 72.13705990673165 for patan
MAX_DISTANCE_KM = 25   # 1 for 

class StudentLoginMixin:
    def handle_student_login(self, request):
        enrollment_no = request.POST.get('enrollment_no')
        student_password = request.POST.get('student_password')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        if not latitude or not longitude:
            messages.error(request, 'Location not provided')
            return render(request, 'login.html')

        if enrollment_no and student_password:
            try:
                student = Students.objects.get(enrollment_no=enrollment_no)
                if student.Student_password == student_password:
                    user_location = (float(latitude), float(longitude))
                    distance = geodesic(ALLOWED_LOCATION, user_location).km
                    if distance > MAX_DISTANCE_KM:
                        messages.error(request, 'You are not within the allowed location')
                        return render(request, 'login.html')

                    if not student.is_active:
                        messages.error(request, 'You are deactivated by admin. Please contact the administration for assistance.')
                        return render(request, 'login.html')

                    device_identifier = request.META.get('HTTP_USER_AGENT')

                    # Check if the current device identifier is already used by another student
                    active_session_same_device = Students.objects.filter(device_identifier=device_identifier).exclude(enrollment_no=enrollment_no).first()

                    if active_session_same_device:
                        messages.error(request, f"Access Denied: You are already associated with {active_session_same_device.enrollment_no}. If this is not your account, please contact your admin")
                        return render(request, 'login.html')

                    # Check if the student's enrollment number is already associated with a different device
                    if student.device_identifier and student.device_identifier != device_identifier:
                        messages.error(request, f"This enrollment number is already associated with another device. If this is not by you, please contact your admin.")
                        return render(request, 'login.html')

                    student.device_identifier = device_identifier
                    student.last_login = timezone.now()
                    student.save()

                    request.session['student_id'] = student.id

                    return redirect('welcome')
                else:
                    messages.error(request, 'Invalid password')
                    return render(request, 'login.html')
            except Students.DoesNotExist:
                messages.error(request, 'There is no such student exist with this enrollment number')
                return render(request, 'login.html')
            except IntegrityError:
                messages.error(request, f"This enrollment number is already associated with another device. If this is not you, please contact your admin.")
                return render(request, 'login.html')

        return render(request, 'login.html', {'error_message': "Please provide your credentials"})