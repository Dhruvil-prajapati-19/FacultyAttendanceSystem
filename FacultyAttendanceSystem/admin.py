from django.contrib import admin
from . import models
from .models import Timetable, HolidayScheduler, Midexamscheduler

import data_wizard
from FacultyAttendanceSystem.models import Students

data_wizard.register(Students)
data_wizard.register(Timetable)
data_wizard.register(HolidayScheduler)

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
    list_display = ('id', 'name', 'short_name')

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
    list_display = ('class_type', 'Student_Class', 'formatted_semester', 'faculty', 'subject', 'room', 'formatted_first_class_date', 'duration', 'start_time', 'end_time', 'formatted_create_date', 'formatted_modified_date')
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

    def formatted_first_class_date(self, obj):
        return obj.first_class_date.strftime("%d/%m/%Y") if obj.first_class_date else '-'
    formatted_first_class_date.short_description = 'First Class Date'

@admin.register(models.TimeTableRollouts)
class TimeTableRolloutsAdmin(admin.ModelAdmin):
    list_display = ('subject', 'faculty', 'room', 'duration', 'class_status', 'formatted_class_date', 'start_time', 'end_time', 'class_attedance')
    list_filter = ('subject', 'faculty', 'room', 'class_status', 'class_attedance', 'class_date')
    search_fields = ('subject__name', 'faculty__name', 'room__room_name', 'class_date', 'short_name', 'faculty__short_name')
    list_editable = ('class_attedance',)

    def formatted_class_date(self, obj):
        return obj.class_date.strftime("%d/%m/%Y")
    formatted_class_date.short_description = 'Class Date'

@admin.register(models.Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'term_date', 'start_date', 'end_date')
    search_fields = ('name',)
    list_filter = ('term_date', 'start_date', 'end_date')

@admin.register(models.EventScheduler)
class EventSchedulerAdmin(admin.ModelAdmin):
    list_display = ('get_faculty_names', 'date', 'start_time', 'end_time', 'Title', 'Description')
    list_filter = ('date', 'start_time', 'end_time', 'Title')
    search_fields = ('Title', 'Description')
    filter_horizontal = ('faculty',)

    def get_faculty_names(self, obj):
        return ", ".join([faculty.name for faculty in obj.faculty.all()])
    get_faculty_names.short_description = 'Faculty'

@admin.register(models.HolidayScheduler)
class HolidaySchedulerAdmin(admin.ModelAdmin):
    list_display = ('date', 'Title')
    list_filter = ('date', 'Title')
    search_fields = ('Title',)

@admin.register(models.Midexamscheduler)
class MidexamschedulerAdmin(admin.ModelAdmin):
    list_display = ('date', 'Title', 'get_semester')
    search_fields = ('Title',)
    list_filter = ('semester',)

    def get_semester(self, obj):
        return obj.semester.name if obj.semester else None
    get_semester.short_description = 'Semester'

@admin.register(Students)
class StudentsAdmin(admin.ModelAdmin):
    list_display = ('enrollment_no', 'student_name', 'get_students_class_name', 'Student_password')
    list_filter = ('Student_Class__Students_class_name',)
    search_fields = ('enrollment_no', 'student_name')
    ordering = ('enrollment_no',)

    def get_students_class_name(self, obj):
        return obj.Student_Class.Students_class_name if obj.Student_Class else ''
    get_students_class_name.short_description = 'Class Name'

@admin.register(models.StudentsRollouts)
class StudentsRolloutsAdmin(admin.ModelAdmin):
    list_display = ('get_student_name', 'get_faculty_name', 'get_subject_name', 'get_room_name',
                    'get_start_time', 'get_end_time', 'formatted_class_date', 'get_class_status', 'student_attendance')

    
    list_filter = ('student__enrollment_no',  'timetable_rollout__subject', 'timetable_rollout__room')
    list_editable = ('student_attendance',)
    search_fields = ('student__enrollment_no', 'student__student_name', 'timetable_rollout__subject__name','timetable_rollout__faculty')
    readonly_fields = ('timetable_rollout', 'student', 'created_by', 'modified_by', 'create_date', 'modified_date')
    search_fields = ('student__enrollment_no', 'student__student_name')
    def get_student_name(self, obj):
        if obj.student:
            return f"{obj.student.student_name} ({obj.student.enrollment_no})"
        return ''

    get_student_name.short_description = 'Student'

    def get_faculty_name(self, obj):
        return obj.timetable_rollout.faculty.name if obj.timetable_rollout.faculty else ''
    get_faculty_name.short_description = 'Faculty'

    def get_subject_name(self, obj):
        return obj.timetable_rollout.subject.name if obj.timetable_rollout.subject else ''
    get_subject_name.short_description = 'Subject'

    def get_room_name(self, obj):
        return obj.timetable_rollout.room.room_name if obj.timetable_rollout.room else ''
    get_room_name.short_description = 'Room'

    def get_start_time(self, obj):
        return obj.timetable_rollout.start_time.strftime('%I:%M %p') if obj.timetable_rollout.start_time else ''
    get_start_time.short_description = 'Start time'

    def get_end_time(self, obj):
        return obj.timetable_rollout.end_time.strftime('%I:%M %p') if obj.timetable_rollout.end_time else ''
    get_end_time.short_description = 'End time'

    def formatted_class_date(self, obj):
        return obj.timetable_rollout.class_date.strftime("%d/%m/%Y") if obj.timetable_rollout.class_date else ''
    formatted_class_date.short_description = 'Formatted class date'

    def get_class_status(self, obj):
        return obj.timetable_rollout.get_class_status_display() if obj.timetable_rollout.class_status else ''
    get_class_status.short_description = 'Class status'

    

@admin.register(models.StudentClass)
class StudentClassAdmin(admin.ModelAdmin):
    list_display = ('Students_class_name', 'semester')
    search_fields = ('Students_class_name',)

@admin.register(models.ActiveSession)
class ActiveSessionAdmin(admin.ModelAdmin):
    pass
