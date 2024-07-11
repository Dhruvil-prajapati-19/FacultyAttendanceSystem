from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.contrib import messages
from FacultyAttendanceSystem.models import ActiveSession, AdminCredentials,  StudentsRollouts,Students, Subject, TimeTableRollouts
from django.core.cache import cache

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
            # Retrieve the faculty_class_id from the cache using the pin_code
            faculty_class_id = cache.get(f'pin_code_{pin_code}')

            if faculty_class_id is None:
                raise ValueError("PIN code not found or expired")
            
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


from django.utils import timezone
from django.utils import timezone

def student_logout_view(request):
    if 'student_id' in request.session:
        student_id = request.session['student_id']
        
        # Retrieve the enrollment number of the student
        try:
            student = Students.objects.get(id=student_id)
            enrollment_no = student.enrollment_no
        except Students.DoesNotExist:
            enrollment_no = None

        if enrollment_no:
            # Update ActiveSession for the logged-out student
            active_session = ActiveSession.objects.filter(enrollment_no=enrollment_no).first()
            if active_session:
                active_session.last_logout = timezone.now()
                active_session.save()
            else:
                # Handle case where no ActiveSession is found
                del request.session['student_id']
                return redirect('login')
                # Example: redirect to login or display an error message

            # Clear session data after updating ActiveSession
            del request.session['student_id']
            messages.success(request, "You have been logged out successfully.")
        else:
            messages.error(request, "No active session found for the student.")
    else:
        messages.error(request, "No enrollment number found ")
        return redirect('login')

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
                messages.error(request, 'Student does not exist for the given enrollment number.')
                return render(request, 'datasheet.html', {'form': form})
            
            # Fetch all rollouts for the student
            rollouts = StudentsRollouts.objects.filter(student=student)
            
            # Dictionary to store attendance data by faculty and subject
            attendance_data = {}
            
            # Calculate attendance data by faculty and subject
            for rollout in rollouts:
                faculty_name = rollout.timetable_rollout.faculty.name if rollout.timetable_rollout.faculty else "Unknown Faculty"
                subject_name = rollout.timetable_rollout.subject.name if rollout.timetable_rollout.subject else "Unknown Subject"
                
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
            
            context = {
                'form': form,
                'student': student,
                'attendance_data': attendance_data,
            }
            return render(request, 'datasheet.html', context)
        
        # If form is invalid, render the form again with validation errors
        return render(request, 'datasheet.html', {'form': form})

def download_all_attendance_data(request):
    # Fetch all unique students
    students = StudentsRollouts.objects.values(
        'student__enrollment_no',
        'student__student_name'
    ).distinct()

    # Initialize the workbook and active sheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance Data"

    # Add the headers
    headers = ["Enrollment No", "Student Name", "Total Attendance", "Total Present", "Attendance Percentage"]
    ws.append(headers)

    # Loop through each student to calculate attendance data
    for student in students:
        enrollment_no = student['student__enrollment_no']
        student_name = student['student__student_name']

        # Calculate total attendance and total present
        total_attendance = StudentsRollouts.objects.filter(student__enrollment_no=enrollment_no).count()
        total_present = StudentsRollouts.objects.filter(student__enrollment_no=enrollment_no, student_attendance=True).count()

        # Calculate attendance percentage
        attendance_percentage = (total_present / total_attendance) * 100 if total_attendance > 0 else 0

        # Append the data to the sheet
        row = [
            enrollment_no,
            student_name,
            total_attendance,
            total_present,
            f"{attendance_percentage:.2f}%"
        ]
        ws.append(row)

    # Save the workbook to a bytes buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    # Create a HTTP response with the Excel file
    response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=AttendanceData.xlsx'

    return response


from openpyxl import Workbook  # type: ignore
from django.http import HttpResponse
from FacultyAttendanceSystem.models import StudentsRollouts
from django.shortcuts import render
from django.http import HttpResponse
from io import BytesIO
from io import BytesIO

def download_attendance_data(request):
    # Fetch the unique subjects, faculties, start times, and end times
    subject_faculty_pairs = StudentsRollouts.objects.values(
        'timetable_rollout__subject__name',
        'timetable_rollout__faculty__name',
        'timetable_rollout__class_id__Student_Class__Students_class_name',
        'timetable_rollout__class_id__semester__name',
        'timetable_rollout__start_time',
        'timetable_rollout__end_time'
    ).distinct()

    # Initialize a dictionary to hold the Excel files
    excel_files = {}

    for pair in subject_faculty_pairs:
        subject_name = pair['timetable_rollout__subject__name']
        faculty_name = pair['timetable_rollout__faculty__name']
        student_class_name = pair['timetable_rollout__class_id__Student_Class__Students_class_name']
        semester_name = pair['timetable_rollout__class_id__semester__name']
        start_time = pair['timetable_rollout__start_time'].strftime('%H-%M')  # Replacing colon with hyphen
        end_time = pair['timetable_rollout__end_time'].strftime('%H-%M')  # Replacing colon with hyphen

        # Fetch all unique class_dates for the current subject, faculty, start time, and end time
        class_dates = StudentsRollouts.objects.filter(
            timetable_rollout__subject__name=subject_name,
            timetable_rollout__faculty__name=faculty_name,
            timetable_rollout__class_id__Student_Class__Students_class_name=student_class_name,
            timetable_rollout__class_id__semester__name=semester_name,
            timetable_rollout__start_time=pair['timetable_rollout__start_time'],
            timetable_rollout__end_time=pair['timetable_rollout__end_time']
        ).values_list('timetable_rollout__class_date', flat=True).distinct().order_by('timetable_rollout__class_date')

        # Create a workbook and a sheet
        wb = Workbook()
        sheet_title = f"{subject_name} - {faculty_name} ({start_time}-{end_time})"
        sheet_title = sheet_title.replace(":", "-")  # Replace invalid characters in sheet title
        ws = wb.active
        ws.title = sheet_title

        # Add the header information
        header_info = [
            f"Subject: {subject_name}",
            f"Faculty: {faculty_name}",
            f"Class: {student_class_name}",
            f"Semester: {semester_name}",
            f"Time: {start_time} - {end_time}"
        ]
        for info in header_info:
            ws.append([info])
        ws.append([])  # Add an empty row for separation

        # Define the headers (excluding the dynamic date columns for now)
        static_headers = ["enrollment_no", "student_name"]

        # Add the dynamic date headers
        dynamic_headers = [date.strftime('%Y-%m-%d') for date in class_dates]
        headers = static_headers + dynamic_headers
        ws.append(headers)

        # Fetch the data for the current subject, faculty, and time with correct date filtering
        student_rollouts = StudentsRollouts.objects.select_related(
            'student',
            'timetable_rollout__subject',
            'timetable_rollout__class_id__semester',
            'timetable_rollout__class_id__Student_Class'
        ).filter(
            timetable_rollout__subject__name=subject_name,
            timetable_rollout__faculty__name=faculty_name,
            timetable_rollout__class_id__Student_Class__Students_class_name=student_class_name,
            timetable_rollout__class_id__semester__name=semester_name,
            timetable_rollout__start_time=pair['timetable_rollout__start_time'],
            timetable_rollout__end_time=pair['timetable_rollout__end_time'],
            timetable_rollout__class_date__in=class_dates  # Filter by the fetched class_dates
        )

        # Create a dictionary to store attendance by student and date
        attendance_data = {}
        for rollout in student_rollouts:
            key = (rollout.student.enrollment_no, rollout.student.student_name)
            if key not in attendance_data:
                attendance_data[key] = {'attendance': {}}
            class_date = rollout.timetable_rollout.class_date.strftime('%Y-%m-%d')
            attendance_data[key]['attendance'][class_date] = "Present" if rollout.student_attendance else "AB"

        # Fill the Excel sheet with data
        for key, data in attendance_data.items():
            row = [
                key[0],  # enrollment_no
                key[1],  # student_name
            ]
            for date in dynamic_headers:
                row.append(data['attendance'].get(date, "A"))  # Default to "A" if no record for the date
            ws.append(row)

        # Save the workbook to a bytes buffer
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        excel_files[f"{subject_name}_{faculty_name}_{start_time}_{end_time}.xlsx"] = buffer

    # Create a HTTP response with the Excel files
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=StudentRollouts.zip'

    from zipfile import ZipFile

    with ZipFile(response, 'w') as zip_file:
        for filename, file_buffer in excel_files.items():
            zip_file.writestr(filename, file_buffer.getvalue())

    return response

#----------------------------------------------------------------
# def download_all_attendance_data(request):
#     # Create a workbook and a sheet
#     wb = Workbook()
#     ws = wb.active
#     ws.title = "StudentRollouts"

#     # Define the headers (excluding the dynamic date columns for now)
#     static_headers = ["semester", "faculty", "student_class", "enrollment_no", "student_name", "subject"]
    
#     # Fetch all unique class_dates from the StudentsRollouts
#     class_dates = StudentsRollouts.objects.values_list('timetable_rollout__class_date', flat=True).distinct().order_by('timetable_rollout__class_date')

#     # Add the dynamic date headers
#     dynamic_headers = [date.strftime('%Y-%m-%d') for date in class_dates]
#     headers = static_headers + dynamic_headers
#     ws.append(headers)

#     # Fetch the data from the database
#     student_rollouts = StudentsRollouts.objects.select_related(
#         'student',
#         'timetable_rollout__subject',
#         'timetable_rollout__class_id__semester',
#         'timetable_rollout__faculty',
#         'timetable_rollout__class_id__Student_Class',
#     )

#     # Create a dictionary to store attendance by student, subject, and date
#     attendance_data = {}
#     for rollout in student_rollouts:
#         key = (rollout.student.enrollment_no, rollout.timetable_rollout.subject.name)
#         if key not in attendance_data:
#             attendance_data[key] = {
#                 'semester': rollout.timetable_rollout.class_id.semester.name,
#                 'faculty': rollout.timetable_rollout.faculty.name,
#                 'student_class': rollout.timetable_rollout.class_id.Student_Class.Students_class_name,
#                 'student_name': rollout.student.student_name,
#                 'subject': rollout.timetable_rollout.subject.name,
#                 'attendance': {}
#             }
#         class_date = rollout.timetable_rollout.class_date.strftime('%Y-%m-%d')
#         attendance_data[key]['attendance'][class_date] = "Present" if rollout.student_attendance else "AB"

#     # Fill the Excel sheet with data
#     for key, data in attendance_data.items():
#         row = [
#             data['semester'],
#             data['faculty'],
#             data['student_class'],
#             key[0],  # enrollment_no
#             data['student_name'],
#             data['subject'],
#         ]
#         for date in dynamic_headers:
#             row.append(data['attendance'].get(date, "A"))  # Default to "A" if no record for the date
#         ws.append(row)

#     # Save the workbook to a bytes buffer
#     from io import BytesIO
#     response = BytesIO()
#     wb.save(response)
#     response.seek(0)

#     # Create a HTTP response with the Excel file
#     http_response = HttpResponse(response, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
#     http_response['Content-Disposition'] = 'attachment; filename=StudentRollouts.xlsx'

#     return http_response
