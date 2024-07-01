#FacultyAttedanceSystem/apps.py
from django.apps import AppConfig
class FacultyAttendanceSystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'FacultyAttendanceSystem'
    verbose_name = 'Faculty Attendance System'

    def ready(self):
        import FacultyAttendanceSystem.signals  # noqa

class StudentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'students'
    verbose_name = 'Students'
