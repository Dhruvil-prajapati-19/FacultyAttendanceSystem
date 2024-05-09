from django.contrib import admin
from django.urls import path
from . import views  
from .decorators import Faculty_login_required  # Import the decorator
admin.site.site_header = "KDPP Faculty Attendance Administration"  
admin.site.site_title = "KDPP Faculty Attendance Administration"  
admin.site.index_title = "KDPP Faculty Attendance Administration"  

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.LoginView.as_view(), name='login'),
    path('index/', Faculty_login_required(views.Attendancesheet.as_view()), name='index'),  
    path('calendar/',  Faculty_login_required(views.Attendancesheet.as_view()), name='calendar_view'),
    path('logout/', views.logout, name='logout'),
    path('download/',  Faculty_login_required(views.download_data), name='download_data'),
    path('index_redirect/', Faculty_login_required(views.index_redirect), name='index_redirect'),
    path('pages-error-404/', Faculty_login_required(views.error_404_view), name='pages-error-404'),
]
