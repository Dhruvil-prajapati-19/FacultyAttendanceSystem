# decorators.py
from django.shortcuts import redirect
from functools import wraps

def Faculty_login_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.session.get('logged_user'): 
            return redirect('/') 
        return view_func(request, *args, **kwargs)
    return wrapped_view

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required

def admin_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view
