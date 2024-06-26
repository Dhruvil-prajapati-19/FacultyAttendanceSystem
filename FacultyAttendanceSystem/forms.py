# forms.py
from django import forms

class XLSXUploadForm(forms.Form):
    xlsx_file = forms.FileField()
