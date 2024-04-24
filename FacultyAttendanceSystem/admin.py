from django.contrib import admin
from django.utils import formats
from . import models

class AdminCredentialsInline(admin.StackedInline):
    model = models.AdminCredentials
    can_delete = False

@admin.register(models.Faculty)
class FacultyAdmin(admin.ModelAdmin):
    inlines = (AdminCredentialsInline,)

@admin.register(models.Subject)
class SubjectAdmin(admin.ModelAdmin):
    pass

@admin.register(models.ClassDuration)
class ClassDurationAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Room)
class RoomAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Timetable)
class TimetableAdmin(admin.ModelAdmin):
    pass

@admin.register(models.TimeTableRollouts)
class TimeTableRolloutsAdmin(admin.ModelAdmin):
    list_display = ('subject', 'faculty', 'room', 'duration', 'class_status', 'formatted_class_date', 'start_time', 'end_time', 'class_attedance')
    list_filter = ('subject', 'faculty', 'room', 'class_status', 'class_attedance', 'class_date')
    search_fields = ('subject__name', 'faculty__name', 'room__room_name', 'class_date')
    list_editable = ('class_attedance',)  # Allow editing class_attedance directly from list display

    def formatted_class_date(self, obj):
        # Format the class_date field in the desired format
        return formats.date_format(obj.class_date, "SHORT_DATE_FORMAT")

    formatted_class_date.short_description = 'Class Date'  # Set the column header

@admin.register(models.Semester)
class SemesterAdmin(admin.ModelAdmin):
    pass
