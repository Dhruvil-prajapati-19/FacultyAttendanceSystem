from django.apps import AppConfig


class FacultyAttendanceSystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'FacultyAttendanceSystem'

    def ready(self):
        import FacultyAttendanceSystem.signals  # noqa
