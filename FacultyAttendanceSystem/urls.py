from django.contrib import admin
from django.urls import path, include
from FacultyAttendanceSystem import views as faculty_views  
from students import views as students_views  
from .decorators import Faculty_login_required  

admin.site.site_header = "KDPP Faculty Attendance Administration"
admin.site.site_title = "KDPP Faculty Attendance Administration Portal"
admin.site.index_title = "Welcome to KDPP Faculty Attendance Administration Portal"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', faculty_views.LoginView.as_view(), name='login'), 
    path('index/', Faculty_login_required(faculty_views.Attendancesheet.as_view()), name='index'),  
    path('Attendancesheet/', Faculty_login_required(faculty_views.Attendancesheet.as_view()), name='calendar_view'),
    path('Students/', Faculty_login_required(students_views.Studentsheet.as_view()), name='Students'),
    path('Student/', Faculty_login_required(students_views.MarkAttendanceButtonView.as_view()), name='MarkAttendanceButton'),
    path('datasheet/', Faculty_login_required(students_views.Datasheet.as_view()), name='datasheet'),
    path('download_attendance/<str:enrollment_no>/', Faculty_login_required(students_views.download_attendance_data), name='download_attendance_data'),
    path('download_all_attendance/', Faculty_login_required(students_views.download_all_attendance_data), name='download_all_attendance_data'),
    path('datawizard/', include('data_wizard.urls')),
    path('logout/', Faculty_login_required(faculty_views.logout), name='logout'),
    path('student-logout/', students_views.student_logout_view, name='studentlogout'),  # Corrected path for student logout
    path('welcome/', students_views.WelcomeView.as_view(), name='welcome'),
    path('download/', Faculty_login_required(faculty_views.download_data), name='download_data'),
    path('index_redirect/', Faculty_login_required(faculty_views.index_redirect), name='index_redirect'),
    path('pages-error-404/', Faculty_login_required(faculty_views.error_404_view), name='pages-error-404'),
    path('punch/', Faculty_login_required(faculty_views.WorkShiftView.punch), name='punch'),
    path('download_work_shift/', Faculty_login_required(faculty_views.Download_WorkShift), name='download_work_shift'),  # Corrected for function-based view
]
