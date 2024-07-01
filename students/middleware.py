from django.http import HttpResponseForbidden

class StudentIPAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            user_ip = request.META['REMOTE_ADDR']
            session_ip = request.session.get('user_ip')
            if session_ip and session_ip != user_ip:
                return HttpResponseForbidden("Access Denied: This IP address is already associated with another user")
        return self.get_response(request)