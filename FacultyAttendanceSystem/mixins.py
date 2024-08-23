# mixing.py
import uuid
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Faculty, Students
from django.utils import timezone
from geopy.distance import geodesic # type: ignore


class FacultyLoginMixin:
    def handle_faculty_login(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            try:
                # Fetch the Faculty object with the matching username
                faculty = Faculty.objects.get(username=username)
                
                # Check if the provided password matches the stored password
                if faculty.password == password:
                    # Set the session for the logged-in user
                    request.session['logged_user'] = faculty.id
                    return redirect('index/')  # Redirect to the desired page after login
                else:
                    messages.error(request, 'Invalid password')
            except Faculty.DoesNotExist:
                messages.error(request, 'Invalid username or password')
        
        # Render the login page again with an error message if credentials are invalid
        return render(request, 'login.html', {'error_message': 'Invalid credentials'})



class StudentLoginMixin:
    def handle_student_login(self, request):
        enrollment_no = request.POST.get('enrollment_no')
        student_password = request.POST.get('student_password')

        if enrollment_no and student_password:
            try:
                # Retrieve the student by enrollment number
                student = Students.objects.get(enrollment_no=enrollment_no)

                # Validate the password
                if student.Student_password == student_password:

                    # Check if the student is active
                    if not student.is_active:
                        messages.error(request, 'You are deactivated by admin. Please contact the administration for assistance.')
                        return render(request, 'login.html')

                    # Store the student ID in the session (optional)
                    request.session['student_id'] = student.id

                    return redirect('welcome')
                else:
                    messages.error(request, 'Invalid password')
                    return render(request, 'login.html')
            except Students.DoesNotExist:
                messages.error(request, 'There is no such student exist with this enrollment number')
                return render(request, 'login.html')

        return render(request, 'login.html', {'error_message': "Please provide your credentials"})