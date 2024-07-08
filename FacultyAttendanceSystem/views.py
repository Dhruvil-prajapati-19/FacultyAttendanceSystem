import random
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import localtime, now
from datetime import datetime, timedelta
from django.http import HttpResponse, HttpResponseRedirect 
from django.utils import timezone
from .models import TimeTableRollouts, AdminCredentials, HolidayScheduler, WorkShift , Students, ActiveSession, StudentsRollouts
from datetime import timedelta
import qrcode # type: ignore
from io import BytesIO
import base64
from django.conf import settings
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import login, logout as auth_logout
from django.views import View
from django.contrib.auth.models import User
from geopy.distance import geodesic # type: ignore

def index_redirect(request):
    return redirect( request,'index/')

def error_404_view(request):
    return render(request, 'pages-error-404.html')



from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from geopy.distance import geodesic # type: ignore
from .models import Students, AdminCredentials, ActiveSession
# Constants for geographic authentication
ALLOWED_LOCATION = (23.859500149431895, 72.13730130104388)
MAX_DISTANCE_KM = 50000000  # Set your desired maximum distance in kilometers
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
                                    messages.error(request, f"Access Denied: Your session is temporarily blocked for 24h from logging into another account and is associated with user {active_session.enrollment_no}. If this is not you, please contact your admin")
                                    return render(request, 'login.html')
                            else:
                                messages.error(request, f"Access Denied: Your session is already associated with user {active_session.enrollment_no}. You can only login as {active_session.enrollment_no}. If this is not you, please contact your admin")
                                return render(request, 'login.html')

                    # Handle session without creating a Django user
                    request.session['student_id'] = student.id

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


class StudentInClassView(View):
    def get(self, request, class_rollout):
        print("Here.......", class_rollout)
        # if request.POST.get('student_rollout'):
        #     attendance = request.POST.get('studentAttendance') == 'true'
        #     student_rollout = request.POST.get('student_rollout')
        #     print(attendance)
        #     print(student_rollout)
        #     try:
        #         student_rollout = StudentsRollouts.objects.get(id=student_rollout)
        #         student_rollout.student_attedance = attendance
        #         student_rollout.save()
        #         messages.success(request, "Attendance has been marked")
        #     except ObjectDoesNotExist as e:
        #         messages.error(request, "Error occurred while marking attendance: " + str(e))
        #     return HttpResponseRedirect(reverse('student-in-class'))


        class_rollout_id = request.POST.get('class_rollout_id')
        print("---------------------------------------------")
        print(class_rollout_id)
        students = StudentsRollouts.objects.filter(timetable_rollout__id=class_rollout)
        present_students = students.filter(student_attendance=True)
        print(present_students.count())
        context = {
            "students": students,
            "present_students": present_students
        }
        return render(request, 'Students.html', context=context)

    def post(self, request, class_rollout):
        attendance = request.POST.get('studentAttendance')        
        if attendance == "true":
            attendance = True
        else:
            attendance = False
        
        student_rollout_id = request.POST.get('student_rollout')
        try:
            student_rollout = StudentsRollouts.objects.get(id=student_rollout_id)
            student_rollout.student_attendance = attendance
            student_rollout.save() 
            messages.info(request, "Attendance has been updated!")
        except Exception as e:
            messages.error(request, "Error occurred while marking attendance: " + str(e))
        return redirect('student-in-class', class_rollout=class_rollout)



class Attendancesheet(View):
    def get(self, request):
        todays_date = timezone.localdate()
        selected_date_str = request.GET.get('weekpicker')
        selected_date = timezone.datetime.strptime(selected_date_str, '%Y-%m-%d').date() if selected_date_str else todays_date
        start_date = selected_date - timedelta(days=selected_date.weekday())
        end_date = start_date + timedelta(days=6)
        faculty_class_id = request.GET.get('classid')
        logged_user = request.session.get('logged_user')

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
        
        pin_code = None

        if faculty_class_id:
            # Generate a random 4-digit PIN
            pin_code = random.randint(1000, 9999)
            # Store the PIN with the current timestamp and faculty_class_id
            request.session['pin_code'] = pin_code
            request.session['pin_code_time'] = timezone.now().timestamp()
            request.session['faculty_class_id'] = faculty_class_id

        class_rollouts = TimeTableRollouts.objects.filter(faculty=faculty, class_date__range=[start_date, end_date])
        holiday_today = HolidayScheduler.objects.filter(date=todays_date).first()

        monday_date = start_date
        tuesday_date = start_date + timedelta(days=1)
        wednesday_date = start_date + timedelta(days=2)
        thursday_date = start_date + timedelta(days=3)
        friday_date = start_date + timedelta(days=4)
        saturday_date = start_date + timedelta(days=5)
        sunday_date = end_date

        final_punch_time = None
        is_punch_out = False
        punch_date_time = None
        try:
            punch_time = WorkShift.objects.filter(faculty=faculty).last()
            if punch_time:
                if punch_time.punch_in and not punch_time.punch_out:
                    final_punch_time = punch_time.punch_in
                    is_punch_out = True
                elif punch_time.punch_in and punch_time.punch_out:
                    final_punch_time = punch_time.punch_out
                punch_date_time = f"{punch_time.date} {final_punch_time.strftime('%H:%M')}"
        except WorkShift.DoesNotExist:
            punch_date_time = None

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
            'monday_classes': class_rollouts.filter(class_date=monday_date),
            'tuesday_classes': class_rollouts.filter(class_date=tuesday_date),
            'wednesday_classes': class_rollouts.filter(class_date=wednesday_date),
            'thursday_classes': class_rollouts.filter(class_date=thursday_date),
            'friday_classes': class_rollouts.filter(class_date=friday_date),
            'saturday_classes': class_rollouts.filter(class_date=saturday_date),
            'sunday_classes': class_rollouts.filter(class_date=sunday_date),
            'holiday_today': holiday_today,
            'total_classes': total_classes,
            'attended_classes': attended_classes,
            'pin_code': pin_code
        }

        return render(request, 'index.html', context)

    def post(self, request):
        attendance = request.POST.get('attendance') == 'true'
        class_rollout_id = request.POST.get('class_rollout_id')
        selected_date_str = request.POST.get('weekpicker')
        
        try:
            class_rollout = TimeTableRollouts.objects.get(id=class_rollout_id)
            class_rollout.class_attedance = attendance
            class_rollout.save()
            messages.success(request, "Attendance has been marked")
        except ObjectDoesNotExist as e:
            messages.error(request, "Error occurred while marking attendance: " + str(e))

        return HttpResponseRedirect(reverse('index') + f'?weekpick={selected_date_str}')

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
    response['Content-Disposition'] = 'attachment; filename=Faculty_Attendance.xlsx'
    
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
    response['Content-Disposition'] = 'attachment; filename=faculty_workshift.xlsx'

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
                        return redirect("AttendanceSheet")
                    
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
        return redirect("AttendanceSheet")
