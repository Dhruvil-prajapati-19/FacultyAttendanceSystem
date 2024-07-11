from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import AdminCredentials, Students, ActiveSession
from django.db import IntegrityError
from geopy.distance import geodesic # type: ignore
from django.utils import timezone
from django.db import IntegrityError

ALLOWED_LOCATION = (23.58729073245821, 72.38227230632735) # 23.85947073496859, 72.13705990673165 for patan
MAX_DISTANCE_KM = 25   # 1 for 
COOLDOWN_PERIOD = timezone.timedelta(hours=24)  

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

class StudentLoginMixin:
    def handle_student_login(self, request):
        enrollment_no = request.POST.get('enrollment_no')
        student_password = request.POST.get('student_password')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        if enrollment_no and student_password:
            if not latitude or not longitude:
                messages.error(request, 'Location not provided')
                return render(request, 'login.html')

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

                    device_identifier = request.COOKIES.get('device_identifier')
                    if not device_identifier:
                        device_identifier = request.META.get('HTTP_USER_AGENT')
                        response = render(request, 'login.html', {'error_message': "Please try again."})
                        response.set_cookie('device_identifier', device_identifier, max_age=None, expires=None)
                        return response

                    active_session_same_device = ActiveSession.objects.filter(device_identifier=device_identifier).exclude(enrollment_no=enrollment_no).first()
                    if active_session_same_device:
                        if active_session_same_device.last_logout:
                            cooldown_end = active_session_same_device.last_logout + COOLDOWN_PERIOD
                            if timezone.now() < cooldown_end:
                                messages.error(request, f"Access Denied: You are already associated with {active_session_same_device.enrollment_no}")
                                return render(request, 'login.html')
                        else:
                            messages.error(request, f"Access Denied: You are already associated with {active_session_same_device.enrollment_no}, If this is not your account, please contact your admin")
                            return render(request, 'login.html')

                    request.session['student_id'] = student.id

                    try:
                        active_session, created = ActiveSession.objects.get_or_create(
                            device_identifier=device_identifier,
                            defaults={'enrollment_no': enrollment_no}
                        )
                        if not created:
                            active_session.enrollment_no = enrollment_no
                            active_session.last_logout = None
                        active_session.save()

                    except IntegrityError:
                        messages.error(request, f"This enrollment number is already associated with another device. If this is not you, please contact your admin.")
                        return render(request, 'login.html')

                    return redirect('welcome')
                else:
                    return render(request, 'login.html', {'error_message': "Invalid password"})
            except Students.DoesNotExist:
                return render(request, 'login.html', {'error_message': "There is no such student exist with this enrollment number"})

        return render(request, 'login.html', {'error_message': "Please provide your credentials"})
