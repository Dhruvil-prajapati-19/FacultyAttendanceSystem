from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Faculty(models.Model):
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class AdminCredentials(models.Model):
    faculty = models.OneToOneField(Faculty, on_delete=models.SET_NULL, null=True)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)

    def __str__(self):
        return self.faculty.name if self.faculty else "No Faculty Assigned"        

class Semester(models.Model):
    term_date = models.CharField(max_length=100, null=True, verbose_name='Term Date')
    name = models.CharField(max_length=120)
    start_date = models.DateField(verbose_name='start term date')
    end_date = models.DateField(verbose_name='end term date')
    
    def __str__(self):
        start_date_str = self.start_date.strftime('%d-%m-%Y')
        end_date_str = self.end_date.strftime('%d-%m-%Y')
        return f'{self.term_date}-{self.name}-{start_date_str} TO {end_date_str}'
    
class Subject(models.Model): 
    name = models.CharField(max_length=200, unique=True)
    short_name = models.CharField(max_length=200)
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, related_name='subjects', null=True)

    def __str__(self):
        return self.name

class ClassDuration(models.Model):
    duration = models.CharField(max_length=20)
    duration_short_name = models.CharField(max_length=20)
    hours = models.IntegerField(null=True)
    minute = models.IntegerField(null=True)

    def __str__(self):
        return self.duration

class Room(models.Model):
    room_name = models.CharField('Room name', max_length=200)

    def __str__(self):
        return self.room_name

class WorkShift(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, verbose_name='faculty_id')
    date = models.DateField(null=True, blank=True, verbose_name="Class Start Time")
    punch_in = models.TimeField(null=True, blank=True, verbose_name='punch in')
    punch_out = models.TimeField(null=True, blank=True, verbose_name='punch out')

    def __str__(self):
        return f"{self.faculty.name} - {self.date} - {self.punch_in} - {self.punch_out}"

class HolidayScheduler(models.Model):
    date = models.DateField(null=True, blank=True, verbose_name="Holiday event")
    Title = models.CharField(max_length=255, blank=True, null=True, verbose_name="Title")
   
    def __str__(self):
        return f"{self.date} - {self.Title}"

class Midexamscheduler(models.Model):
    date = models.DateField(null=True, blank=True, verbose_name="Mid Exam Date")
    Title = models.CharField(max_length=255, blank=True, null=True, verbose_name="Mid Exam Title")
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, related_name='related_midexams', null=True)

    def __str__(self):
        return f"{self.date} - {self.Title}"
    
class StudentClass(models.Model):
    Students_class_name = models.CharField(max_length=200, verbose_name='Class Name', null=True)
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, related_name='related_classes', null=True , blank=True)
    
    def __str__(self):
        return f"{self.Students_class_name} - {self.semester}"

class Students(models.Model):
    enrollment_no = models.CharField(max_length=20, verbose_name='Enrollment Number', null=True, blank=True)
    student_name = models.CharField(max_length=100, verbose_name='Student Name', null=True, blank=True)
    Student_Class = models.ForeignKey(StudentClass, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Student Class')
    Student_password = models.CharField(max_length=50, verbose_name='Student Password', blank=True, null=True) # Unique device identifier
    last_login = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name='Is Active')


    def __str__(self):
        return f'{self.student_name} ({self.enrollment_no}) - {self.Student_Class.Students_class_name if self.Student_Class else ""}'


class Timetable(models.Model):
    CLASS_TYPE_CHOICES = (
        ('lecture', 'lecture'),
        ('lab', 'lab'),
        ('lab-A1', 'lab-A1'),
        ('lab-A2', 'lab-A2'),
        ('lab-A3', 'lab-A3'),
        ('lab-A4', 'lab-A4'),
        ('lab-B1', 'lab-B1'),
        ('lab-B2', 'lab-B2'),
        ('lab-B3', 'lab-B3'),
        ('lab-B4', 'lab-B4'),
        ('lab-C1', 'lab-C1'),
        ('lab-C2', 'lab-C2'),
        ('lab-C3', 'lab-C3'),
        ('lab-C4', 'lab-C4'),
    )
    Student_Class = models.ForeignKey(StudentClass, on_delete=models.CASCADE, blank=True, null=True)
    class_type = models.CharField('Class Type', max_length=200, null=True, blank=True, choices=CLASS_TYPE_CHOICES, default='scheduled')
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True)
    first_class_date = models.DateField(verbose_name='First Class of the semester')
    faculty = models.ForeignKey(Faculty, verbose_name='faculty_id', null=True, on_delete=models.SET_NULL)
    subject = models.ForeignKey(Subject, verbose_name='subject', related_name='subject', on_delete=models.SET_NULL, null=True)
    room = models.ForeignKey(Room, verbose_name='Room', related_name='room', on_delete=models.SET_NULL, blank=True, null=True)
    duration = models.ForeignKey(ClassDuration, related_name='class_definition_duration', on_delete=models.SET_NULL, null=True)
    create_date = models.DateTimeField('Class definition create date', auto_now_add=True, null=True)
    created_by_user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='class_definition_creator')
    modified_date = models.DateTimeField('Class definition modified date', auto_now=True, null=True)
    modified_by_user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='class_definition_modifier')
    start_time = models.TimeField(null=True, blank=True, verbose_name="Class Start Time")
    end_time = models.TimeField(null=True, blank=True, verbose_name="Class End Time")

    def __str__(self):
        semester_name = self.semester.name if self.semester else ""
        subject_short_name = self.subject.short_name if self.subject else ""
        faculty_name = self.faculty.name if self.faculty else ""
        room_name = self.room.room_name if self.room else ""
        time_range = f"{self.start_time.strftime('%I:%M %p')} TO {self.end_time.strftime('%I:%M %p')}"
        return f'{semester_name} - {subject_short_name} - {faculty_name} - {room_name} - {time_range}'

class TimeTableRollouts(models.Model):
    STATUSES_CHOICES = (
        ('scheduled', 'scheduled'),
        ('cancelled', 'cancelled'),
        ('break', 'break'),
        ('discontinued', 'discontinued'),
    )
    faculty = models.ForeignKey(Faculty, verbose_name='faculty_id', null=True, on_delete=models.SET_NULL)
    room = models.ForeignKey(Room, null=True, blank=True, on_delete=models.SET_NULL)
    subject = models.ForeignKey(Subject, null=True, blank=True, verbose_name='Subject', on_delete=models.SET_NULL)
    duration = models.ForeignKey(ClassDuration, null=True, blank=True, related_name='class_rollout', on_delete=models.SET_NULL)
    class_id = models.ForeignKey(Timetable, null=True, blank=True, related_name='class_rollout', on_delete=models.CASCADE, verbose_name='Class definition')
    class_status = models.CharField('Class status', max_length=200, null=True, blank=True, choices=STATUSES_CHOICES, default='scheduled')
    class_attedance = models.BooleanField(default=False, verbose_name='Faculty Attendance')
    created_by = models.ForeignKey(User, related_name='class_created_by', null=True, on_delete=models.SET_NULL)
    modified_by = models.ForeignKey(User, related_name='class_modified_by', null=True, blank=True, on_delete=models.SET_NULL)
    create_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(default=timezone.now, null=True)
    start_time = models.TimeField('Start time', null=True, blank=True)
    end_time = models.TimeField('End time', null=True, blank=True)
    class_date = models.DateField('Class date', null=True, blank=True)

    def __str__(self):
        subject = self.subject.name if self.subject else ""
        start_time_str = self.start_time.strftime("%H:%M") if self.start_time else ""
        end_time_str = self.end_time.strftime("%H:%M") if self.end_time else ""
        return f"Class for: {subject} at {self.class_date} from {start_time_str} to {end_time_str}"

class StudentsRollouts(models.Model):
    timetable_rollout = models.ForeignKey(TimeTableRollouts, related_name='student_rollouts', on_delete=models.CASCADE, null=True, verbose_name='Timetable Rollout')
    student = models.ForeignKey(Students, verbose_name='Student', null=True, on_delete=models.SET_NULL)
    student_attendance = models.BooleanField(default=False, verbose_name='Student Attendance')
    created_by = models.ForeignKey(User, related_name='student_class_created_by', null=True, on_delete=models.SET_NULL)
    modified_by = models.ForeignKey(User, related_name='student_class_modified_by', null=True, blank=True, on_delete=models.SET_NULL)
    create_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(default=timezone.now, null=True)

    def __str__(self):
        subject_name = self.timetable_rollout.subject.name if self.timetable_rollout and self.timetable_rollout.subject else "No Subject"
        class_date = self.timetable_rollout.class_date if self.timetable_rollout and self.timetable_rollout.class_date else "No Date"
        start_time_str = self.timetable_rollout.start_time.strftime("%H:%M") if self.timetable_rollout and self.timetable_rollout.start_time else "No Start Time"
        end_time_str = self.timetable_rollout.end_time.strftime("%H:%M") if self.timetable_rollout and self.timetable_rollout.end_time else "No End Time"
        return f"Class for: {subject_name} on {class_date} from {start_time_str} to {end_time_str}"


