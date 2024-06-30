from django.http import HttpResponseForbidden
from django.utils import timezone
from .models import ActiveSession

COOLDOWN_PERIOD = timezone.timedelta(minutes=60)

class StudentIPAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            user_ip = request.META['REMOTE_ADDR']
            enrollment_no = request.user.username
            
            # Check for existing active session
            active_session = ActiveSession.objects.filter(enrollment_no=enrollment_no).first()
            if active_session:
                if active_session.ip_address != user_ip:
                    if active_session.last_logout:
                        cooldown_end = active_session.last_logout + COOLDOWN_PERIOD
                        if timezone.now() < cooldown_end:
                            return HttpResponseForbidden(f"Access Denied: This IP address ({user_ip}) is temporarily blocked from logging into another account and is associated with user {enrollment_no}")
                    else:
                        return HttpResponseForbidden(f"Access Denied: This IP address ({user_ip}) is already associated with user {enrollment_no}. You can only login as {enrollment_no}")
            
            # Update or create active session
            if active_session:
                active_session.ip_address = user_ip
                active_session.save()
            else:
                active_session = ActiveSession(enrollment_no=enrollment_no, ip_address=user_ip)
                active_session.save()

        response = self.get_response(request)
        return response
