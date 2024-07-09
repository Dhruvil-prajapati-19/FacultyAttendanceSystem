from django.http import HttpResponseForbidden
from ipware import get_client_ip # type: ignore
from FacultyAttendanceSystem.models import ActiveSession

class StudentIPAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            client_ip, is_routable = get_client_ip(request)
            session_ip = request.session.get('user_ip')
            if session_ip and session_ip != client_ip:
                return HttpResponseForbidden("Access Denied: This IP address is already associated with another user")
            
            # Ensure the session IP matches the active session record
            active_session = ActiveSession.objects.filter(ip_address=client_ip).first()
            if active_session and active_session.enrollment_no != request.user.username:
                return HttpResponseForbidden("Access Denied: This IP address is already associated with another enrollment number")

            # Store the client's IP address in the session if not already set
            if not session_ip:
                request.session['user_ip'] = client_ip

        return self.get_response(request)
