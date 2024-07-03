from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from datetime import datetime, timedelta, timezone 
import qrcode # type: ignore
from io import BytesIO
import base64
from FacultyAttendanceSystem import settings 
from FacultyAttendanceSystem.models import ActiveSession, AdminCredentials, Faculty, Room, StudentsRollouts, Students
from django.core import signing


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
        students_rollouts = StudentsRollouts.objects.none()  # Initialize as empty queryset
        qr_code_data = None

        if selected_room_id:
            selected_room = get_object_or_404(Room, id=selected_room_id)

            if faculty:
                students_rollouts = StudentsRollouts.objects.filter(
                    faculty=faculty,
                    room=selected_room,
                    class_date__gte=start_date,
                    class_date__lte=end_date,
                )

                # Generate QR code data with a token
                qr_data = f'{faculty.id},{selected_room.id},{selected_date_str}'
                token = signing.dumps(qr_data, key=settings.QR_SECRET_KEY)
                qr_img = qrcode.make(token)
                buffer = BytesIO()
                qr_img.save(buffer, format="PNG")
                qr_code_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

        context = {
            'success': True,
            'faculty_name': faculty,
            'todays_date': todays_date,
            'rooms': Room.objects.all(),
            'selected_date': selected_date.strftime('%Y-%m-%d'),
            'monday_date': start_date.strftime('%a %d %b, %Y'),
            'tuesday_date': (start_date + timedelta(days=1)).strftime('%a %d %b, %Y'),
            'wednesday_date': (start_date + timedelta(days=2)).strftime('%a %d %b, %Y'),
            'thursday_date': (start_date + timedelta(days=3)).strftime('%a %d %b, %Y'),
            'friday_date': (start_date + timedelta(days=4)).strftime('%a %d %b, %Y'),
            'saturday_date': (start_date + timedelta(days=5)).strftime('%a %d %b, %Y'),
            'sunday_date': end_date.strftime('%a %d %b, %Y'),
            'monday_classes': students_rollouts.filter(class_date=start_date),
            'tuesday_classes': students_rollouts.filter(class_date=start_date + timedelta(days=1)),
            'wednesday_classes': students_rollouts.filter(class_date=start_date + timedelta(days=2)),
            'thursday_classes': students_rollouts.filter(class_date=start_date + timedelta(days=3)),
            'friday_classes': students_rollouts.filter(class_date=start_date + timedelta(days=4)),
            'saturday_classes': students_rollouts.filter(class_date=start_date + timedelta(days=5)),
            'sunday_classes': students_rollouts.filter(class_date=end_date),
            'selected_room': selected_room,
            'qr_code_data': qr_code_data,
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

            # Check if there are multiple students to mark attendance for
            unique_enrollment_numbers = students_to_mark.values_list('student__enrollment_no', flat=True).distinct()
            if len(unique_enrollment_numbers) > 1:
                # Get the start and end time of the class
                class_start_time = students_to_mark.first().start_time
                class_end_time = students_to_mark.first().end_time

                # Get current time
                current_time = datetime.now().time()

                for student_rollout in students_to_mark:
                    # Check if current time is between start and end time of the class
                    if class_start_time <= current_time <= class_end_time:
                        student_rollout.student_attendance = True
                        student_rollout.save()
                    else:
                        messages.error(request, f"Cannot mark attendance for student {student_rollout.student} outside class time.")
            else:
                # Mark attendance without time restriction for single student scenario
                for student_rollout in students_to_mark:
                    student_rollout.student_attendance = True
                    student_rollout.save()

            messages.success(request, "Attendance successfully marked")
            return HttpResponseRedirect(reverse('Students') + f'?weekpicker={selected_date}&room={selected_room_id}')

class MarkAttendanceButtonView(View):
    def post(self, request):
        student_rollout_id = request.POST.get('student_rollout_id')
        attendance = request.POST.get('attendance') == 'true'
        
        try:
            class_rollout = StudentsRollouts.objects.get(id=student_rollout_id)
            class_rollout.student_attendance = attendance
            class_rollout.save()
            messages.success(request, "Attendance has been marked")
        except StudentsRollouts.DoesNotExist:
            messages.error(request, "Student rollout not found.")
        
        return redirect("Students")
        
class WelcomeView(View):
    def get(self, request):
        if request.user.is_authenticated:
            enrollment_no = request.user.username  # Assuming enrollment_no is the username
            try:
                student = Students.objects.get(enrollment_no=enrollment_no)
                context = {
                    'student_name': student.student_name,
                    'enrollment_no': student.enrollment_no,
                }
                return render(request, 'welcome.html', context)
            except Students.DoesNotExist:
                messages.error(request, "Student not found")
                return redirect('login')
        else:
            return redirect('login')

    def post(self, request):
        attendance_input = request.POST.get('attendanceInput')
        selected_date_str = request.POST.get('selected_date')
        selected_room_id = request.POST.get('selected_room')
        selected_faculty_id = request.POST.get('selected_faculty')

        if not attendance_input or not selected_date_str or not selected_room_id or not selected_faculty_id:
            messages.error(request, "Incomplete Qr code provided")
            return redirect("welcome")

        selected_room = get_object_or_404(Room, id=selected_room_id)
        enrollment_numbers = [enrollment.strip() for enrollment in attendance_input.split(',') if enrollment.strip()]

        try:
            faculty = get_object_or_404(Faculty, id=selected_faculty_id)
        except Faculty.DoesNotExist:
            messages.error(request, "Faculty not found from Qr code")
            return redirect("welcome")

        students_to_mark = StudentsRollouts.objects.filter(
            class_date=selected_date_str,
            room=selected_room,
            faculty=faculty,
            student__enrollment_no__in=enrollment_numbers
        )

        for student_rollout in students_to_mark:
            student_rollout.student_attendance = True
            student_rollout.save()

        messages.success(request, "Attendance successfully marked")
        return redirect("welcome")


from django.contrib.auth import logout as auth_logout
from django.utils import timezone
def student_logout_view(request):
    if request.user.is_authenticated:
        user_ip = request.META['REMOTE_ADDR']
        active_session = ActiveSession.objects.filter(ip_address=user_ip).first()
        if active_session:
            active_session.last_logout = timezone.now()
            active_session.save()
        auth_logout(request)
    return redirect('login')
       
from FacultyAttendanceSystem.models import Students, StudentsRollouts, AdminCredentials 
from .forms import EnrollmentForm
from django.http import HttpResponse
from openpyxl import Workbook # type: ignore
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
