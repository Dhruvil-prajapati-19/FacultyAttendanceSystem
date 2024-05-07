from django.contrib import admin
from django.urls import path
from . import views  # Import views from the same directory

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login, name='login'),
    path('index.html', views.index, name='index'),
     path('index/', views.calendar, name='calendar'), 
]
