from django.contrib import admin
from django.urls import path
from . import views  
from .decorators import Faculty_login_required  # Import the decorator

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.LoginView.as_view(), name='login'),
    path('index/', Faculty_login_required(views.Attendancesheet.as_view()), name='index'),  # Apply the decorator to Attendancesheet
    path('calendar/',  Faculty_login_required(views.Attendancesheet.as_view()), name='calendar_view'),
    path('logout/', views.logout, name='logout'),
    path('download/',  Faculty_login_required(views.download_data), name='download_data'),
]
