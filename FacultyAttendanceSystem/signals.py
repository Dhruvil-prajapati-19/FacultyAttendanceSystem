from datetime import timedelta
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import (
    Timetable, TimeTableRollouts, Students, StudentsRollouts,
    EventScheduler, HolidayScheduler, Midexamscheduler
)

@receiver(post_save, sender=Timetable)
def create_or_update_rollouts(sender, instance, created, **kwargs):
    if created:
        create_rollouts(instance)
    else:
        update_rollouts(instance)

@receiver(post_delete, sender=Timetable)
def delete_rollouts(sender, instance, **kwargs):
    TimeTableRollouts.objects.filter(class_id=instance).delete()
    StudentsRollouts.objects.filter(timetable_rollout__class_id=instance).delete()

def create_rollouts(instance):
    semester_end_date = instance.semester.end_date
    first_class_date = instance.first_class_date
    class_definition = instance

    while first_class_date <= semester_end_date:
        # Create TimeTableRollouts for faculty
        create_timetable_rollout(class_definition, first_class_date)

        # Create StudentsRollouts for students
        create_students_rollouts(class_definition, first_class_date)

        # Move to the next week
        first_class_date += timedelta(weeks=1)

def update_rollouts(instance):
    # Update TimeTableRollouts for faculty
    update_timetable_rollouts(instance)

    # Update StudentsRollouts for students
    update_students_rollouts(instance)

def create_timetable_rollout(instance, first_class_date):
    class_rollout = TimeTableRollouts(
        faculty=instance.faculty,
        room=instance.room,
        subject=instance.subject,
        duration=instance.duration,
        class_id=instance,
        class_status='scheduled',
        created_by=instance.created_by_user,
        modified_by=instance.modified_by_user,
        start_time=instance.start_time,
        end_time=instance.end_time,
        class_date=first_class_date,
    )
    class_rollout.save()

def update_timetable_rollouts(instance):
    rollouts = TimeTableRollouts.objects.filter(class_id=instance)
    for rollout in rollouts:
        rollout.faculty = instance.faculty
        rollout.room = instance.room
        rollout.subject = instance.subject
        rollout.duration = instance.duration
        rollout.start_time = instance.start_time
        rollout.end_time = instance.end_time
        rollout.modified_by = instance.modified_by_user
        rollout.save()

def create_students_rollouts(instance, first_class_date):
    students = Students.objects.filter(Student_Class=instance.Student_Class)
    if not students.exists():
        return  # Handle case where no students are found for the class

    for student in students:
        student_rollout = StudentsRollouts(
            timetable_rollout=TimeTableRollouts.objects.get(class_id=instance, class_date=first_class_date),
            student=student,
            student_attendance=False,
            created_by=instance.created_by_user,
            modified_by=instance.modified_by_user,
        )
        student_rollout.save()

def update_students_rollouts(instance):
    students_rollouts = StudentsRollouts.objects.filter(timetable_rollout__class_id=instance)

    for rollout in students_rollouts:
        rollout.timetable_rollout.room = instance.room
        rollout.timetable_rollout.subject = instance.subject
        rollout.timetable_rollout.duration = instance.duration
        rollout.timetable_rollout.start_time = instance.start_time
        rollout.timetable_rollout.end_time = instance.end_time
        rollout.modified_by = instance.modified_by_user
        rollout.save()

@receiver(post_save, sender=EventScheduler)
@receiver(post_delete, sender=EventScheduler)
def handle_event_scheduler(sender, instance, **kwargs):
    event_date = instance.date
    event_start_time = instance.start_time
    event_end_time = instance.end_time
    event_faculty = instance.faculty.all()

    # Remove classes for the specified faculty within the event time
    for faculty in event_faculty:
        TimeTableRollouts.objects.filter(
            faculty=faculty,
            class_date=event_date,
            start_time__gte=event_start_time,
            end_time__lte=event_end_time
        ).delete()

@receiver(post_save, sender=HolidayScheduler)
@receiver(post_delete, sender=HolidayScheduler)
def handle_holiday_scheduler(sender, instance, **kwargs):
    holiday_date = instance.date

    # Remove all classes on the holiday date
    TimeTableRollouts.objects.filter(class_date=holiday_date).delete()
    StudentsRollouts.objects.filter(timetable_rollout__class_date=holiday_date).delete()

@receiver(post_save, sender=Midexamscheduler)
@receiver(post_delete, sender=Midexamscheduler)
def handle_midexamscheduler(sender, instance, **kwargs):
    midexam_date = instance.date
    for_semester = instance.semester

    TimeTableRollouts.objects.filter(class_date=midexam_date, class_id__semester=for_semester).delete()
    StudentsRollouts.objects.filter(timetable_rollout__class_date=midexam_date, timetable_rollout__class_id__semester=for_semester).delete()
