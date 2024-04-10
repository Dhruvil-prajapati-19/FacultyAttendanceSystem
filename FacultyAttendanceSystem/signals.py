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
