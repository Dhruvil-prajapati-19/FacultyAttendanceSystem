from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from django.core.exceptions import ObjectDoesNotExist
from .models import AdminCredentials, EventScheduler, Faculty, HolidayScheduler, TimeTableRollouts, WorkShift
from django.utils.timezone import localtime, now
from .decorators import Faculty_login_required
from datetime import datetime, timedelta
from django.http import HttpResponse
from openpyxl import Workbook # type: ignore


'''def error_404(request, exception):
    return render(request, 'pages-error-404.html', status=404)'''

def logout(request):
    if 'logged_user' in request.session:
        del request.session['logged_user']
        messages.success(request, "You have been logged out successfully.")
    return redirect('/') 

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

def index_redirect(request):
    return redirect('index/')


def error_404_view(request):
    return render(request, 'pages-error-404.html')


class LoginView(View):

    def get(self, request):
        return render(request, 'login.html')
    
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            admin_credentials = AdminCredentials.objects.get(username=username)

            if admin_credentials.password == password:
                logged_user = admin_credentials.faculty.id
                request.session['logged_user'] = logged_user
                messages.success(request, f'You have successfully logged in as {admin_credentials.faculty}')
                return redirect('index/')
            else:
                error_message = 'Invalid password'
        except AdminCredentials.DoesNotExist:
            error_message = 'Invalid username or password'

        messages.error(request, error_message)
        return render(request, 'login.html')


class Attendancesheet(View):
    
    def get(self, request):
        todays_date = datetime.now().date()
        selected_date_str = request.GET.get('weekpicker')
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d') if selected_date_str else todays_date
        start_date = selected_date - timedelta(days=selected_date.weekday())
        end_date = start_date + timedelta(days=6)

        logged_user = request.session.get('logged_user')

        total_classes = 0
        attended_classes = 0
        faculty = None

        if logged_user:
            try:
                faculty = AdminCredentials.objects.get(id=logged_user).faculty
                total_classes = TimeTableRollouts.objects.filter(faculty=faculty).count()
                attended_classes = TimeTableRollouts.objects.filter(faculty=faculty, class_attedance=True).count()
            except AdminCredentials.DoesNotExist:
                pass
         
        today_date = datetime.date.today()
        class_rollouts = TimeTableRollouts.objects.filter(faculty=faculty, class_date__gte=start_date, class_date__lte=end_date)
        event_today = EventScheduler.objects.filter(date=today_date, faculty=faculty)
        holiday_today = HolidayScheduler.objects.filter(date=today_date).first()

        
        monday_date = start_date
        tuesday_date = start_date + timedelta(days=1)
        wednesday_date = start_date + timedelta(days=2)
        thursday_date = start_date + timedelta(days=3)
        friday_date = start_date + timedelta(days=4)
        saturday_date = start_date + timedelta(days=5)
        sunday_date = end_date

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
        try:
            punch_time = WorkShift.objects.filter(faculty=faculty).last()
            if punch_time:
                if punch_time.punch_in is not None and punch_time.punch_out is None:
                    final_punch_time = punch_time.punch_in
                    is_punch_out = True
                else:
                    if punch_time.punch_in and punch_time.punch_out is not None:
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
            'monday_date': start_date.strftime('%a %d %b, %Y'),
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
            'event_today': event_today,
            'holiday_today': holiday_today,
            'total_classes': total_classes,
            'attended_classes': attended_classes,
            'total_classes': total_classes,
            'attended_classes': attended_classes,
        }

        return render(request, 'index.html', context)
    
    def post(self, request):
         attendance = request.POST.get('attendance')
         if attendance == 'true':
            attendance = True
         else:
            attendance = False
         class_rollout_id = request.POST.get('class_rollout_id')
         try:
            class_rollout = TimeTableRollouts.objects.get(id=class_rollout_id)
            class_rollout.class_attedance = attendance
            class_rollout.save()
            messages.success(request, "Attendance has been marked")
         except ObjectDoesNotExist as e:
            messages.error(request, "Error occurred while marking attendance")

         return redirect("calendar_view")
        
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
