
# forms.py
from django import forms

class EnrollmentForm(forms.Form):
    enrollment_no = forms.CharField(label='Enrollment Number', max_length=20)
