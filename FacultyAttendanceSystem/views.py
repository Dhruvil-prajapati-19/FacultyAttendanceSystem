from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from .models import AdminCredentials, HolidayScheduler, TimeTableRollouts, WorkShift
from django.utils.timezone import localtime, now
from datetime import datetime, timedelta
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from .models import TimeTableRollouts, AdminCredentials, Room, HolidayScheduler, WorkShift
from datetime import timedelta
import qrcode
from io import BytesIO
import base64
from django.conf import settings
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

def index_redirect(request):
    return redirect('index/')

def error_404_view(request):
    return render(request, 'pages-error-404.html')

def Students(request):
    return render(request, 'Students.html')

from django.utils import timezone
from django.contrib.auth import login, logout as auth_logout
from django.views import View
from .models import Students, AdminCredentials, ActiveSession
from django.contrib.auth.models import User
from django.http import HttpResponse
from geopy.distance import geodesic # type: ignore
from .models import AdminCredentials, Students, ActiveSession, User

# Constants for geographic authentication
ALLOWED_LOCATION = (23.850872, 72.117408)
MAX_DISTANCE_KM = 50  # Set your desired maximum distance in kilometers
COOLDOWN_PERIOD = timezone.timedelta(minutes=1440)  # Adjust as needed

class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        # Handle Faculty login
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            try:
                admin_credentials = AdminCredentials.objects.get(username=username)
                if admin_credentials.password == password:
                    logged_user = admin_credentials.faculty.id
                    request.session['logged_user'] = logged_user
                    messages.success(request, f'You have successfully logged in as {admin_credentials.faculty}')
                    return redirect('index/')
                else:
                    messages.error(request, 'Invalid password')
                    return render(request, 'login.html')
            except AdminCredentials.DoesNotExist:
                messages.error(request, 'Invalid username or password')
                return render(request, 'login.html')

        # Handle Student login
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

                if student.Student_password == student_password:  # Directly compare passwords
                    user_ip = request.META['REMOTE_ADDR']

                    # Check if the student is within the allowed location
                    user_location = (float(latitude), float(longitude))
                    distance = geodesic(ALLOWED_LOCATION, user_location).km

                    if distance > MAX_DISTANCE_KM:
                        messages.error(request, 'You are not within the allowed location')
                        return render(request, 'login.html')

                    active_session = ActiveSession.objects.filter(ip_address=user_ip).first()
                    if active_session:
                        if active_session.enrollment_no != enrollment_no:
                            if active_session.last_logout:
                                cooldown_end = active_session.last_logout + COOLDOWN_PERIOD
                                if timezone.now() < cooldown_end:
                                    messages.error(request, f"Access Denied: Your session is temporarily blocked for 24h from logging into another account and is associated with user {active_session.enrollment_no} if it not you then contact your admin")
                                    return render(request, 'login.html')
                            else:
                                messages.error(request, f"Access Denied: Your session is already associated with user {active_session.enrollment_no}. You can only login as {active_session.enrollment_no} if it not you then contact your admin")
                                return render(request, 'login.html')

                    # Authenticate user
                    django_user, created = User.objects.get_or_create(username=enrollment_no)
                    login(request, django_user)

                    # Update active session
                    if active_session:
                        active_session.enrollment_no = enrollment_no
                        active_session.last_logout = None
                    else:
                        active_session = ActiveSession(enrollment_no=enrollment_no, ip_address=user_ip)
                    active_session.save()

                    return redirect('welcome')
                else:
                    messages.error(request, "Invalid password")
                    return render(request, 'login.html')
            except Students.DoesNotExist:
                messages.error(request, "Invalid enrollment number or password")
                return render(request, 'login.html')

        # If neither student nor faculty login data is provided
        messages.error(request, "Please provide your credentials")
        return render(request, 'login.html')

def logout(request):
    if 'logged_user' in request.session:
        del request.session['logged_user']
        messages.success(request, "You have been logged out successfully.")
    return redirect('/') 

from django.conf import settings
from .models import AdminCredentials, TimeTableRollouts, HolidayScheduler, WorkShift
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.views import View
from datetime import timedelta
from io import BytesIO
import qrcode
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

class Attendancesheet(View):
    def get(self, request):
        qr_selected_room = request.GET.get('xqr')
        todays_date = timezone.localdate()
        selected_date_str = request.GET.get('weekpicker')
        selected_date = timezone.datetime.strptime(selected_date_str, '%Y-%m-%d').date() if selected_date_str else todays_date
        start_date = selected_date - timedelta(days=selected_date.weekday())
        end_date = start_date + timedelta(days=6)  

        logged_user = request.session.get('logged_user')
        print(qr_selected_room)
        print(f"QR Selected Room: {qr_selected_room}")  # Check if this prints the expected value

        total_classes = 0
        attended_classes = 0
        faculty = None

        if logged_user:
            try:
                admin_credentials = AdminCredentials.objects.get(id=logged_user)
                faculty = admin_credentials.faculty
                total_classes = TimeTableRollouts.objects.filter(faculty=faculty).count()
                attended_classes = TimeTableRollouts.objects.filter(faculty=faculty, class_attedance=True).count()
            except AdminCredentials.DoesNotExist:
                pass

        qr_code_data = None

        if faculty and qr_selected_room:
            qr_data = f'{faculty.id},{qr_selected_room}'
            encrypted_token = self.encrypt_data(qr_data)
            # Generate QR code image
            qr_img = qrcode.make(encrypted_token)
            buffer = BytesIO()
            qr_img.save(buffer, format="PNG")
            qr_code_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
            print(f"QR Code Data: {qr_code_data}")  # Check if this prints the QR code data

        class_rollouts = TimeTableRollouts.objects.filter(faculty=faculty, class_date__range=[start_date, end_date])
        holiday_today = HolidayScheduler.objects.filter(date=todays_date).first()

        # Prepare dates for each day of the week (you can adjust as needed)
        monday_date = start_date
        tuesday_date = start_date + timedelta(days=1)
        wednesday_date = start_date + timedelta(days=2)
        thursday_date = start_date + timedelta(days=3)
        friday_date = start_date + timedelta(days=4)
        saturday_date = start_date + timedelta(days=5)
        sunday_date = end_date

        # Filter class rollouts for each day of the week (adjust as needed)
        monday_classes = class_rollouts.filter(class_date=monday_date)
        tuesday_classes = class_rollouts.filter(class_date=tuesday_date)
        wednesday_classes = class_rollouts.filter(class_date=wednesday_date)
        thursday_classes = class_rollouts.filter(class_date=thursday_date)
        friday_classes = class_rollouts.filter(class_date=friday_date)
        saturday_classes = class_rollouts.filter(class_date=saturday_date)
        sunday_classes = class_rollouts.filter(class_date=sunday_date)

        final_punch_time = None
        is_punch_out = False
        punch_date_time = None
        
        # Logic for punch time if needed
        # Replace with your own logic as per requirements

        context = {
            'faculty_name': faculty,
            'punch_time': punch_date_time,
            'is_punch_out': is_punch_out,
            'todays_date': todays_date,
            'success': True,
            'selected_date': selected_date.strftime('%Y-%m-%d'),
            'monday_date': monday_date.strftime('%a %d %b, %Y'),
            'tuesday_date': tuesday_date.strftime('%a %d %b, %Y'),
            'wednesday_date': wednesday_date.strftime('%a %d %b, %Y'),
            'thursday_date': thursday_date.strftime('%a %d %b, %Y'),
            'friday_date': friday_date.strftime('%a %d %b, %Y'),
            'saturday_date': saturday_date.strftime('%a %d %b, %Y'),
            'sunday_date': sunday_date.strftime('%a %d %b, %Y'),
            'monday_classes': monday_classes,
            'tuesday_classes': tuesday_classes,
            'wednesday_classes': wednesday_classes,
            'thursday_classes': thursday_classes,
            'friday_classes': friday_classes,
            'saturday_classes': saturday_classes,
            'sunday_classes': sunday_classes,
            'holiday_today': holiday_today,
            'total_classes': total_classes,
            'attended_classes': attended_classes,
            'qr_code_data': qr_code_data
        }

        return render(request, 'index.html', context)

from openpyxl import Workbook # type: ignore
def download_data(request):
    logged_user = request.session.get('logged_user')


    class_rollouts = TimeTableRollouts.objects.filter(faculty__id=logged_user)

    # Create a new workbook
    wb = Workbook()
    ws = wb.active
    
    # Add headers
    ws.append(['Faculty Signature', 'Room', 'Subject', 'Attendance','Class Date'])
    
    # Add data to the worksheet
    for rollout in class_rollouts:
        faculty_name = rollout.faculty.name if rollout.faculty else ''
        room_name = rollout.room.room_name if rollout.room else ''
        subject_name = rollout.subject.name if rollout.subject else ''
        attendance = 'Present' if rollout.class_attedance else 'Absent'
        class_date = rollout.class_date.strftime('%Y-%m-%d') if rollout.class_date else ''
        ws.append([faculty_name, room_name, subject_name, attendance,class_date])

    # Create a response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=timetable_rollouts.xlsx'
    
    # Save the workbook to the response
    wb.save(response)
    
    return response

def Download_WorkShift(request):
    logged_user = request.session.get('logged_user')

    # Filter WorkShift entries for the logged-in faculty
    work_shift_entries = WorkShift.objects.filter(faculty__id=logged_user)

    # Create a new workbook
    wb = Workbook()
    ws = wb.active

    # Add headers
    ws.append(['Faculty', 'Date', 'Punch In', 'Punch Out'])

    # Add data to the worksheet
    for entry in work_shift_entries:
        faculty_name = entry.faculty.name if entry.faculty else ''
        date = entry.date.strftime('%Y-%m-%d') if entry.date else ''
        punch_in = entry.punch_in.strftime('%H:%M:%S') if entry.punch_in else ''
        punch_out = entry.punch_out.strftime('%H:%M:%S') if entry.punch_out else ''
        ws.append([faculty_name, date, punch_in, punch_out])

    # Create a response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=work_shift_entries.xlsx'

    # Save the workbook to the response
    wb.save(response)

    return response

from django.shortcuts import render, redirect
class WorkShiftView(View):
    def punch(request):
        logged_user = request.session.get('logged_user')
        if logged_user:
            try:
                faculty = AdminCredentials.objects.get(id=logged_user).faculty
                current_time = localtime(now())
                try:
                    existing_entry = WorkShift.objects.get(faculty=faculty, date=current_time.date())
                    if existing_entry.punch_in and existing_entry.punch_out is not None:
                        messages.info(request, "Punch already exist for today!")
                        return redirect("calendar_view")
                    
                    if existing_entry.punch_in is not None and existing_entry.punch_out is None:
                        existing_entry.punch_out = current_time.time()
                        existing_entry.save()
                except WorkShift.DoesNotExist as e:
                    WorkShift.objects.create(faculty=faculty, date=current_time.date(), punch_in=current_time.time())
                    messages.success(request, "Punch in successful")
    
            except ObjectDoesNotExist:
                messages.error(request, "Faculty not found.")
        else:
            messages.error(request, "Faculty not logged in.")
        return redirect("calendar_view")



