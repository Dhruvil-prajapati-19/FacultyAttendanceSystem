from django.shortcuts import render,redirect
from .models import AdminCredentials



def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Fetch admin credentials based on the provided username
        admin_credentials = AdminCredentials.objects.filter(username=username).first()
        
        if admin_credentials and admin_credentials.password == password:
            return redirect('index')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    else:
        return render(request, 'login.html')
 


def index(request):
    # Add your view logic here
    return render(request, 'index.html') 




