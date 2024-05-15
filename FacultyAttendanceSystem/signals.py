from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Timetable, TimeTableRollouts
from datetime import timedelta

@receiver(post_save, sender=Timetable)
def create_rollouts_for_timetable(sender, instance, created, **kwargs):
    if created:
        semester_end_date = instance.semester.end_date
        first_class_date = instance.first_class_date
        class_definition = instance

        while first_class_date <= semester_end_date:
            if first_class_date > semester_end_date:
                break  

            class_rollout = TimeTableRollouts(
                faculty=class_definition.faculty,
                room=class_definition.room,
                subject=class_definition.subject,
                duration=class_definition.duration,
                class_id=class_definition,
                class_status='scheduled',
                created_by=class_definition.created_by_user,
                modified_by=class_definition.modified_by_user,
                start_time=class_definition.start_time,
                end_time=class_definition.end_time,
                class_date=first_class_date,
            )
            class_rollout.save()

            # Move to the next week
            first_class_date += timedelta(weeks=1)

@receiver(post_save, sender=Timetable)
def update_rollouts_for_timetable(sender, instance, created, **kwargs):
    if not created:
        # Get the related TimeTableRollouts objects for this Timetable instance
        rollouts = TimeTableRollouts.objects.filter(class_id=instance)

        # Update the rollouts based on the modified Timetable instance
        for rollout in rollouts:
            rollout.faculty = instance.faculty
            rollout.room = instance.room
            rollout.subject = instance.subject
            rollout.duration = instance.duration
            rollout.start_time = instance.start_time
            rollout.end_time = instance.end_time
            rollout.modified_by = instance.modified_by_user
            rollout.save()

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import EventScheduler, HolidayScheduler, TimeTableRollouts

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
