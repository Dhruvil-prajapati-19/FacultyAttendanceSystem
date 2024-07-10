from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import localtime, now
from datetime import  timedelta
from django.http import HttpResponse, HttpResponseRedirect 
from .models import TimeTableRollouts, AdminCredentials, HolidayScheduler, WorkShift , Students, ActiveSession, StudentsRollouts ,BannedStudent ,Faculty
from datetime import timedelta
from django.urls import reverse
from django.views import View 
from django.core.cache import cache
import random
from django.utils import timezone
def index_redirect(request):
    return redirect( request,'index/')

def error_404_view(request):
    return render(request, 'pages-error-404.html')

from geopy.distance import geodesic # type: ignore
# Constants for geographic authentication
ALLOWED_LOCATION = (23.58729073245821, 72.38227230632735) # 23.85947073496859, 72.13705990673165 for patan
MAX_DISTANCE_KM = 25   # 1 for 
COOLDOWN_PERIOD = timezone.timedelta(hours=24)  

class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        enrollment_no = request.POST.get('enrollment_no')
        student_password = request.POST.get('student_password')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        if username and password:
            return self.handle_faculty_login(request, username, password)

        if enrollment_no and student_password:
            return self.handle_student_login(request, enrollment_no, student_password, latitude, longitude)

        return render(request, 'login.html', {'error_message': "Please provide your credentials"})

    def handle_faculty_login(self, request, username, password):
        try:
            admin_credentials = AdminCredentials.objects.get(username=username)
            if admin_credentials.password == password:
                logged_user = admin_credentials.faculty.id
                request.session['logged_user'] = logged_user
                messages.success(request, f'You have successfully logged in as {admin_credentials.faculty}')
                return redirect('index')
            else:
                messages.error(request, 'Invalid password')
        except AdminCredentials.DoesNotExist:
            messages.error(request, 'Invalid username or password')
        return render(request, 'login.html', {'error_message': 'Invalid username or password'})

    def handle_student_login(self, request, enrollment_no, student_password, latitude, longitude):
        if not latitude or not longitude:
            messages.error(request, 'Location not provided')
            return render(request, 'login.html')

        if self.is_student_banned(request, enrollment_no):
            return render(request, 'login.html')

        device_identifier = self.get_device_identifier(request)
        if not device_identifier:
            response = render(request, 'login.html', {'error_message': "Please try again."})
            response.set_cookie('device_identifier', request.META.get('HTTP_USER_AGENT'))
            return response

        try:
            student = Students.objects.get(enrollment_no=enrollment_no)
            if student.Student_password == student_password:
                if self.is_within_allowed_location(latitude, longitude):
                    if self.is_device_in_cooldown(device_identifier, enrollment_no):
                        messages.error(request, f"Access Denied: You are already associated with another account")
                        return render(request, 'login.html')

                    request.session['student_id'] = student.id
                    self.update_active_session(request, device_identifier, enrollment_no)  # Pass enrollment_no here
                    return redirect('welcome')
                else:
                    messages.error(request, 'You are not within the allowed location')
            else:
                messages.error(request, "Invalid password")
        except Students.DoesNotExist:
            messages.error(request, "No such student exists with this enrollment number")

        return render(request, 'login.html')

    def is_student_banned(self, request, enrollment_no):
        try:
            banned_student = BannedStudent.objects.get(enrollment_no=enrollment_no)
            if banned_student.is_ban_active():
                remaining_ban_time = banned_student.banned_at + timedelta(hours=banned_student.duration_hours) - timezone.now()
                hours_remaining = remaining_ban_time.seconds // 3600
                minutes_remaining = (remaining_ban_time.seconds % 3600) // 60
                messages.error(request, f'You are banned by {banned_student.faculty.name} for [{hours_remaining}H:{minutes_remaining}M.]')
                return True
        except BannedStudent.DoesNotExist:
            return False

    def get_device_identifier(self, request):
        return request.COOKIES.get('device_identifier') or request.META.get('HTTP_USER_AGENT')

    def is_within_allowed_location(self, latitude, longitude):
        user_location = (float(latitude), float(longitude))
        distance = geodesic(ALLOWED_LOCATION, user_location).km
        return distance <= MAX_DISTANCE_KM

    def is_device_in_cooldown(self, device_identifier, enrollment_no):
        active_session_same_device = ActiveSession.objects.filter(device_identifier=device_identifier).exclude(enrollment_no=enrollment_no).first()
        if active_session_same_device:
            if active_session_same_device.last_logout:
                cooldown_end = active_session_same_device.last_logout + COOLDOWN_PERIOD
                if timezone.now() < cooldown_end:
                    return True
        return False

    def update_active_session(self, request, device_identifier, enrollment_no):  # Ensure enrollment_no is passed
        try:
            active_session, created = ActiveSession.objects.get_or_create(device_identifier=device_identifier, defaults={'enrollment_no': enrollment_no})
            if not created:
                active_session.enrollment_no = enrollment_no
                active_session.last_logout = None
            active_session.save()
        except IntegrityError:
            messages.error(request, "This enrollment number is already associated with another device. If this is not you, please contact your admin.")
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
            # Store the PIN and faculty_class_id in the cache for 300 seconds (5 minutes)
            cache.set(f'pin_code_{pin_code}', faculty_class_id, timeout=300)

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

def logout(request):
    if 'logged_user' in request.session:
        del request.session['logged_user']
        messages.success(request, "You have been logged out successfully.")
    return redirect('/') 


class StudentInClassView(View):
    def get(self, request, class_rollout):

        class_rollout_id = request.POST.get('class_rollout_id')
        students = StudentsRollouts.objects.filter(timetable_rollout__id=class_rollout)
        present_students = students.filter(student_attendance=True)
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
