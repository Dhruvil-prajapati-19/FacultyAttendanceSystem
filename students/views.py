from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from datetime import datetime
import base64
from django.conf import settings
from FacultyAttendanceSystem.models import ActiveSession, AdminCredentials, Faculty, Room, StudentsRollouts,Students, TimeTableRollouts
from django.db.models import Count
from datetime import datetime

class Studentsheet(View):
    def get(self, request):
        return render(request, 'Students.html')

class WelcomeView(View):
    def get(self, request):
        student_id = request.session.get('student_id')
        
        if student_id:
            try:
                student = Students.objects.get(id=student_id)
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
        pin_code = request.POST.get('pin_code')

        try:
            stored_pin = request.session.get('pin_code')
            stored_pin_time = request.session.get('pin_code_time')
            faculty_class_id = request.session.get('faculty_class_id')

            if stored_pin is None or stored_pin_time is None or faculty_class_id is None:
                raise ValueError("PIN code not found or expired")
            
            current_time = timezone.now().timestamp()
            if current_time - stored_pin_time > 300:
                raise ValueError("PIN code expired")
            
            if int(pin_code) != stored_pin:
                raise ValueError("Invalid PIN code")
            
            student = Students.objects.get(enrollment_no=attendance_input)
            student_rollout = StudentsRollouts.objects.get(timetable_rollout__id=faculty_class_id, student=student)
            student_rollout.student_attendance = True
            student_rollout.save()

            messages.success(request, "Attendance successfully marked")
        except ValueError as ve:
            messages.error(request, str(ve))
        except Students.DoesNotExist:
            messages.error(request, "Student not found with the given enrollment number")
        except StudentsRollouts.DoesNotExist:
            messages.error(request, "Entry not found")
        except Exception as e:
            messages.error(request, f"Error marking attendance: {str(e)}")

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
