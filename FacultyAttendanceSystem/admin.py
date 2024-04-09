from django.contrib import admin
from .models import Faculty, AdminCredentials, Timetable, TimetableEntry, Subject, ClassDuration, Room, TimeTableRollouts

class AdminCredentialsInline(admin.StackedInline):
    model = AdminCredentials
    can_delete = False

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    inlines = (AdminCredentialsInline,)

@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    pass  # You can customize this admin class as needed

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    pass

@admin.register(ClassDuration)
class ClassDurationAdmin(admin.ModelAdmin):
    pass

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    pass

@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    pass

@admin.register(TimeTableRollouts)
class TimeTableRolloutsAdmin(admin.ModelAdmin):
    pass
