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

def student_login_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.session.get('student_id'):
            return redirect('/') 
        return view_func(request, *args, **kwargs)
    return wrapped_view
