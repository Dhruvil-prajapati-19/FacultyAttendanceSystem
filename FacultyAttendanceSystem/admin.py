from django.contrib import admin
from . import models

@admin.register(models.AdminCredentials)
class AdminCredentialsAdmin(admin.ModelAdmin):
    list_display = ['faculty', 'username']
    search_fields = ['faculty__name', 'faculty__short_name']

@admin.register(models.ClassDuration)
class ClassDurationAdmin(admin.ModelAdmin):
    list_display = ('duration', 'duration_short_name', 'hours', 'minute')

@admin.register(models.Faculty)
class FacultyAdmin(admin.ModelAdmin):
    search_fields = ('name', 'short_name')
    list_display = ('name', 'short_name')

@admin.register(models.Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'semester')
    search_fields = ('name', 'short_name')

@admin.register(models.Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_name',)


@admin.register(models.WorkShift)
class WorkshiftAdmin(admin.ModelAdmin):
    list_display = ('faculty', 'formatted_date', 'formatted_punch_in', 'formatted_punch_out')
    search_fields = ('faculty__name', 'faculty__short_name') 
    list_filter = ('faculty__name',) 
    
#custom design: 
    def formatted_date(self, obj):
        """Custom method to display the date in dd/mm/yyyy format."""
        if obj.date:
            return obj.date.strftime('%d/%m/%Y')
        else:
            return '-'
    formatted_date.short_description = 'Date'

    def formatted_punch_in(self, obj):
        """Custom method to display the punch in time with seconds."""
        if obj.punch_in:
            return obj.punch_in.strftime('%H:%M:%S')
        else:
            return '-'
    formatted_punch_in.short_description = 'Punch In'

 
    def formatted_punch_out(self, obj):
      """Custom method to display the punch out time with seconds."""
      if obj.punch_out:
        return obj.punch_out.strftime('%H:%M:%S')
      else:
        return '-'
    formatted_punch_out.short_description = 'Punch Out'

    
@admin.register(models.Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('class_type', 'formatted_semester', 'faculty', 'subject', 'room', 'duration', 'start_time', 'end_time', 'formatted_create_date', 'formatted_modified_date')
    list_filter = ('class_type', 'semester', 'faculty', 'subject', 'room', 'create_date', 'modified_date')
    search_fields = ('semester__name', 'faculty__name', 'subject__name', 'room__room_name', 'faculty__short_name')

    def formatted_semester(self, obj):
        if obj.semester:
            parts = obj.semester.name.split('-')
            return f'{parts[0]}-{parts[1]}' if len(parts) >= 2 else parts[0]
        else:
            return '-'

    formatted_semester.short_description = 'Semester'

    def formatted_create_date(self, obj):
        return obj.create_date.strftime("%d/%m/%Y")

    formatted_create_date.short_description = 'Class Definition Create Date'

    def formatted_modified_date(self, obj):
        return obj.modified_date.strftime("%d/%m/%Y")

    formatted_modified_date.short_description = 'Class Definition Modified Date'

@admin.register(models.TimeTableRollouts)
class TimeTableRolloutsAdmin(admin.ModelAdmin):
    list_display = ('subject', 'faculty', 'room', 'duration', 'class_status', 'formatted_class_date', 'start_time', 'end_time', 'class_attedance')
    list_filter = ('subject', 'faculty', 'room', 'class_status', 'class_attedance', 'class_date')
    search_fields = ('subject__name', 'faculty__name', 'room__room_name', 'class_date' , 'short_name' ,'faculty__short_name')
    list_editable = ('class_attedance',)

    def formatted_class_date(self, obj):
        return obj.class_date.strftime("%d/%m/%Y")

    formatted_class_date.short_description = 'Class Date'

@admin.register(models.Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date')
    search_fields = ('name',)
    list_filter = ('start_date', 'end_date')
