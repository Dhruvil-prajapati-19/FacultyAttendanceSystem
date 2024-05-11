from django.contrib import admin
from django.urls import path
from . import views  
from .decorators import Faculty_login_required  # Import the decorator

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.LoginView.as_view(), name='login'),
    path('index/', Faculty_login_required(views.Attendancesheet.as_view()), name='index'),  
    path('calendar/',  Faculty_login_required(views.Attendancesheet.as_view()), name='calendar_view'),
    path('logout/', Faculty_login_required(views.logout), name='logout'),
    path('download/',  Faculty_login_required(views.download_data), name='download_data'),
    path('index_redirect/', Faculty_login_required(views.index_redirect), name='index_redirect'),
    path('pages-error-404/', Faculty_login_required(views.error_404_view), name='pages-error-404'),
    path('punch_in/', Faculty_login_required(views.WorkShiftView.punch_in), name='punch_in'),
    path('punch_out/', Faculty_login_required(views.WorkShiftView.punch_out), name='punch_out'),
    path('download_work_shift/', Faculty_login_required(views.Download_WorkShift), name='download_work_shift'),
]
