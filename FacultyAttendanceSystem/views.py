from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from django.core.exceptions import ObjectDoesNotExist
from .models import AdminCredentials, TimeTableRollouts, WorkShift
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

        class_rollouts = TimeTableRollouts.objects.filter(faculty__id=logged_user, class_date__gte=start_date,
                                                          class_date__lte=end_date)

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

        context = {
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
   
    def punch_in(request):
        logged_user = request.session.get('logged_user')
        if logged_user:
            try:
                faculty = AdminCredentials.objects.get(id=logged_user).faculty
                # Get the current time in the local timezone
                current_time = localtime(now())
                # Check if a punch-in entry already exists for today
                existing_entry = WorkShift.objects.filter(faculty=faculty, date=current_time.date()).exists()
                if existing_entry:
                    messages.warning(request, "Punch in already recorded for today.")
                else:
                    # Create a new punch-in entry
                    WorkShift.objects.create(faculty=faculty, date=current_time.date(), punch_in=current_time.time())
                    messages.success(request, "Punch in successful")
            except ObjectDoesNotExist:
                messages.error(request, "Faculty not found.")
        else:
            messages.error(request, "Faculty not logged in.")
        return redirect("calendar_view")

    def punch_out(request):
        logged_user = request.session.get('logged_user')
        if logged_user:
            try:
                faculty = AdminCredentials.objects.get(id=logged_user).faculty
                work_shift = WorkShift.objects.filter(faculty=faculty).last()
                if work_shift:
                    # Get the current time in the local timezone
                    current_time = localtime(now())
                    # Check if a punch-out entry already exists for today
                    existing_entry = WorkShift.objects.filter(faculty=faculty, date=current_time.date(), punch_out__isnull=False).exists()
                    if existing_entry:
                        messages.warning(request, "Punch out already recorded for today.")
                    else:
                        # Update the punch-out time
                        work_shift.punch_out = current_time.time()
                        work_shift.save()
                        messages.success(request, "Punch out successful")
                else:
                    messages.error(request, "Punch out failed. No punch in recorded.")
            except ObjectDoesNotExist:
                messages.error(request, "Faculty not found.")
        else:
            messages.error(request, "Faculty not logged in.")
        return redirect("calendar_view")
