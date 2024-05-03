from django.contrib import admin
from django.urls import path
from . import views  # Import views from the same directory

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login, name='login'),
    path('index/', views.calendar, name='calendar'),
    path('', views.calendar, name='index'), 
    path('toggle-attendance/<int:class_rollout_id>/', views.toggle_attendance, name='toggle_attendance')
]
