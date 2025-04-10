from django.contrib import admin
from django.urls import path, include
from . import views  
from .decorators import Faculty_login_required  
admin.site.site_header = "KDPP Faculty Attendance Administration"
admin.site.site_title = "KDPP Faculty Attendance Administration Portal"
admin.site.index_title = "Welcome to KDPP Faculty Attendance Administration Portal"
#handler404 = 'FacultyAttendanceSystem.views.error_404'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.LoginView.as_view(), name='login'),
    path('index/', Faculty_login_required(views.Attendancesheet.as_view()), name='index'),  
    path('Attendancesheet/',  Faculty_login_required(views.Attendancesheet.as_view()), name='calendar_view'),
    path('Students/',  Faculty_login_required(views.Studentsheet.as_view()), name='Students'),
    path('qr-students/',views.qr_students, name='qr_students'),
    path('qr_code/', include('qr_code.urls', namespace='qr_code')), 
    path('datasheet/',Faculty_login_required(views.Datasheet.as_view()), name='datasheet'),
    path('download_attendance/<str:enrollment_no>/', Faculty_login_required(views.download_attendance_data), name='download_attendance_data'),
    path('download_all_attendance/', Faculty_login_required(views.download_all_attendance_data), name='download_all_attendance_data'),
    path('datawizard/', include('data_wizard.urls')),
    path('logout/', Faculty_login_required(views.logout), name='logout'),
    path('download/',  Faculty_login_required(views.download_data), name='download_data'),
    path('index_redirect/', Faculty_login_required(views.index_redirect), name='index_redirect'),
    path('pages-error-404/', Faculty_login_required(views.error_404_view), name='pages-error-404'),
    path('punch/', Faculty_login_required(views.WorkShiftView.punch), name='punch'),
    path('download_work_shift/', Faculty_login_required(views.Download_WorkShift), name='download_work_shift'),
]