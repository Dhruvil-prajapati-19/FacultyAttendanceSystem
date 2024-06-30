from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.urls import reverse
from django.views import View
from django.core.exceptions import ObjectDoesNotExist
from .models import AdminCredentials, Students, StudentsRollouts, HolidayScheduler, Room, StudentsRollouts, TimeTableRollouts, WorkShift
from django.utils.timezone import localtime, now
from datetime import datetime, timedelta
from django.http import HttpResponse, HttpResponseRedirect
from openpyxl import Workbook # type: ignore
from .forms import EnrollmentForm 

def error_404(request, exception):
    return render(request, 'pages-error-404.html', status=404)

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

def Students(request):
    return render(request, 'Students.html')

def upload(request):
    return render(request, 'upload.html')

def qr_students(request):
    return render(request, 'qrstudents.html')

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

        class_rollouts = TimeTableRollouts.objects.filter(faculty=faculty, class_date__gte=start_date, class_date__lte=end_date)
        holiday_today = HolidayScheduler.objects.filter(date=todays_date)
        
        # if holiday_today.exists():  # Check if there is a holiday scheduled for today
        #    holiday_today = holiday_today.first().Title

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
            'holiday_today': holiday_today,
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
            messages.error(request, "Error occurred while marking attendance",e)

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

class Studentsheet(View):
    def get(self, request):
        todays_date = datetime.now().date()
        selected_date_str = request.GET.get('weekpicker')
        selected_room_id = request.GET.get('room')
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d') if selected_date_str else todays_date
        start_date = selected_date - timedelta(days=selected_date.weekday())
        end_date = start_date + timedelta(days=6)

        logged_user = request.session.get('logged_user')
        faculty = None
        if logged_user:
            try:
                faculty = AdminCredentials.objects.get(id=logged_user).faculty
            except AdminCredentials.DoesNotExist:
                pass

        selected_room = None
        if selected_room_id:
            selected_room = get_object_or_404(Room, id=selected_room_id)

        Students_rollouts = StudentsRollouts.objects.filter(
            faculty=faculty,
            room=selected_room,
            class_date__gte=start_date,
            class_date__lte=end_date,
        )

        context = {
            'faculty_name': faculty,
            'todays_date': todays_date,
            'success': True,
            'selected_date': selected_date.strftime('%Y-%m-%d'),
            'monday_date': start_date.strftime('%a %d %b, %Y'),
            'tuesday_date': (start_date + timedelta(days=1)).strftime('%a %d %b, %Y'),
            'wednesday_date': (start_date + timedelta(days=2)).strftime('%a %d %b, %Y'),
            'thursday_date': (start_date + timedelta(days=3)).strftime('%a %d %b, %Y'),
            'friday_date': (start_date + timedelta(days=4)).strftime('%a %d %b, %Y'),
            'saturday_date': (start_date + timedelta(days=5)).strftime('%a %d %b, %Y'),
            'sunday_date': end_date.strftime('%a %d %b, %Y'),
            'monday_classes': Students_rollouts.filter(class_date=start_date),
            'tuesday_classes': Students_rollouts.filter(class_date=start_date + timedelta(days=1)),
            'wednesday_classes': Students_rollouts.filter(class_date=start_date + timedelta(days=2)),
            'thursday_classes': Students_rollouts.filter(class_date=start_date + timedelta(days=3)),
            'friday_classes': Students_rollouts.filter(class_date=start_date + timedelta(days=4)),
            'saturday_classes': Students_rollouts.filter(class_date=start_date + timedelta(days=5)),
            'sunday_classes': Students_rollouts.filter(class_date=end_date),
            'rooms': Room.objects.all(),
            'selected_room': selected_room,
        }

        return render(request, 'Students.html', context)

    def post(self, request):
        attendance_input = request.POST.get('attendanceInput')
        selected_date = request.POST.get('selected_date')
        selected_room_id = request.POST.get('selected_room')

        if not attendance_input or not selected_date or not selected_room_id:
            messages.error(request, "Incomplete attendance data provided")
            return redirect("Students")

        selected_room = get_object_or_404(Room, id=selected_room_id)
        enrollment_numbers = [enrollment.strip() for enrollment in attendance_input.split(',') if enrollment.strip()]

        students_to_mark = StudentsRollouts.objects.filter(
            class_date=selected_date,
            room=selected_room,
            student__enrollment_no__in=enrollment_numbers
        )

        for student_rollout in students_to_mark:
            student_rollout.student_attendance = True
            student_rollout.save()
            # Optionally, you can uncomment the following line to show a success message for each student marked present
            # messages.success(request, f"Attendance marked for student {student_rollout.student.enrollment_no}")

        # Redirect back to the same selected_date page after processing
        return HttpResponseRedirect(reverse('Students') + f'?weekpicker={selected_date}&room={selected_room_id}')

from django.shortcuts import render, get_object_or_404
from django.views import View
from django.core.exceptions import ObjectDoesNotExist
from .models import Students, StudentsRollouts, AdminCredentials 
from .forms import EnrollmentForm
from django.shortcuts import render, redirect
from django.http import HttpResponse

class Datasheet(View):
    def get(self, request):
        form = EnrollmentForm()
        logged_user = request.session.get('logged_user')
        faculty = None
        if logged_user:
            try:
                faculty = AdminCredentials.objects.get(id=logged_user).faculty
            except AdminCredentials.DoesNotExist:
                pass
        context = {
            'form': form,
            'faculty_name': faculty
        }
        return render(request, 'datasheet.html', context)

    def post(self, request):
        form = EnrollmentForm(request.POST)
        
        if form.is_valid():
            enrollment_no = form.cleaned_data['enrollment_no']
            
            try:
                student = Students.objects.get(enrollment_no=enrollment_no)
            except Students.DoesNotExist:
                error_message = 'Student does not exist for the given enrollment number.'
                return render(request, 'datasheet.html', {'form': form, 'error_message': error_message})
            
            # Fetch all rollouts for the student
            rollouts = StudentsRollouts.objects.filter(student=student)
            
            # Dictionary to store attendance data by faculty and subject
            attendance_data = {}
            
            # Calculate attendance data by faculty and subject
            for rollout in rollouts:
                faculty_name = rollout.faculty.name if rollout.faculty else "Unknown Faculty"
                subject_name = rollout.subject.name if rollout.subject else "Unknown Subject"
                
                # Initialize faculty entry if not exists
                if faculty_name not in attendance_data:
                    attendance_data[faculty_name] = {}
                
                # Initialize subject entry under faculty if not exists
                if subject_name not in attendance_data[faculty_name]:
                    attendance_data[faculty_name][subject_name] = {'attended': 0, 'total': 0}
                
                # Count attendance based on the student_attendance flag
                if rollout.student_attendance:
                    attendance_data[faculty_name][subject_name]['attended'] += 1
                attendance_data[faculty_name][subject_name]['total'] += 1
            
            # Calculate total attendance across all subjects
            total_attended = sum(sum(data['attended'] for data in subjects.values()) for subjects in attendance_data.values())
            total_classes = sum(sum(data['total'] for data in subjects.values()) for subjects in attendance_data.values())
            
            context = {
                'form': form,
                'student': student,
                'attendance_data': attendance_data,
                'total_attended': total_attended,
                'total_classes': total_classes,
            }
            return render(request, 'datasheet.html', context)
        
        # If form is invalid, render the form again with validation errors
        return render(request, 'datasheet.html', {'form': form})

    def create_excel_workbook(self, attendance_data, student, total_attended, total_classes):
        wb = Workbook()
        ws = wb.active
        ws.title = "Student Attendance"
        
        # Add headers to the worksheet
        ws.append(["Student Name", "Enrollment Number", "Total Attendance (%)"])
        
        # Calculate total attendance percentage
        if total_classes > 0:
            total_attendance_percentage = (total_attended / total_classes) * 100
        else:
            total_attendance_percentage = 0
        
        # Append student data
        ws.append([student.student_name, student.enrollment_no, total_attendance_percentage])
        
        # Save the workbook to a HttpResponse
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={student.student_name}_Attendance.xlsx'
        
        wb.save(response)
        return response

def download_attendance_data(request, enrollment_no):
        try:
            student = Students.objects.get(enrollment_no=enrollment_no)
        except Students.DoesNotExist:
            return HttpResponse("Student not found.", status=404)

        rollouts = StudentsRollouts.objects.filter(student=student)

        wb = Workbook()
        ws = wb.active
        ws.title = "Attendance Data"

        # Header row
        ws.append(["Faculty", "Subject", "Attended", "Total Classes", "Percentage"])

        attendance_data = {}
        for rollout in rollouts:
            faculty_name = rollout.faculty.name if rollout.faculty else "Unknown Faculty"
            subject_name = rollout.subject.name if rollout.subject else "Unknown Subject"
            
            if faculty_name not in attendance_data:
                attendance_data[faculty_name] = {}
            
            if subject_name not in attendance_data[faculty_name]:
                attendance_data[faculty_name][subject_name] = {'attended': 0, 'total': 0}
            
            if rollout.student_attendance:
                attendance_data[faculty_name][subject_name]['attended'] += 1
            attendance_data[faculty_name][subject_name]['total'] += 1
        
        for faculty, subjects in attendance_data.items():
            for subject, data in subjects.items():
                attended = data['attended']
                total = data['total']
                percentage = (attended / total * 100) if total > 0 else 0
                ws.append([faculty, subject, attended, total, percentage])

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=attendance_{enrollment_no}.xlsx'

        wb.save(response)
        return response

def download_all_attendance_data(request):
    students = Students.objects.all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance Data"

    # Header row
    ws.append(["Enrollment Number", "Student Name", "Faculty", "Subject", "Attended", "Total Classes", "Percentage"])

    for student in students:
        rollouts = StudentsRollouts.objects.filter(student=student)
        attendance_data = {}
        for rollout in rollouts:
            faculty_name = rollout.faculty.name if rollout.faculty else "Unknown Faculty"
            subject_name = rollout.subject.name if rollout.subject else "Unknown Subject"
            
            if faculty_name not in attendance_data:
                attendance_data[faculty_name] = {}
            
            if subject_name not in attendance_data[faculty_name]:
                attendance_data[faculty_name][subject_name] = {'attended': 0, 'total': 0}
            
            if rollout.student_attendance:
                attendance_data[faculty_name][subject_name]['attended'] += 1
            attendance_data[faculty_name][subject_name]['total'] += 1
        
        for faculty, subjects in attendance_data.items():
            for subject, data in subjects.items():
                attended = data['attended']
                total = data['total']
                percentage = (attended / total * 100) if total > 0 else 0
                ws.append([student.enrollment_no, student.student_name, faculty, subject, attended, total, percentage])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=all_students_attendance.xlsx'

    wb.save(response)
    return response