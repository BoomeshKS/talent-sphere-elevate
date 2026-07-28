from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        role = request.POST.get('role', 'candidate')
        
        # Validation
        if not username or not email or not password:
            messages.error(request, 'All fields are required!')
            return render(request, 'accounts/register.html')
        
        if password != password2:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return render(request, 'accounts/register.html')
        
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters!')
            return render(request, 'accounts/register.html')
        
        # Create user
        try:
            user = User.objects.create_user(
                username=username, 
                email=email, 
                password=password
            )
            user.profile.role = role
            user.save()
            
            messages.success(request, f'Registration successful! You are registered as {role}. Please login.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return render(request, 'accounts/register.html')
    
    return render(request, 'accounts/register.html')

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Username and password are required!')
            return render(request, 'accounts/login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password!')
    
    return render(request, 'accounts/login.html')

@login_required
def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def dashboard(request):
    user = request.user
    role = user.profile.role
    
    if role == 'recruiter':
        context = {
            'user': user,
            'total_jobs': 5,
            'total_applications': 24,
            'shortlisted': 8,
            'interviews_scheduled': 3,
            'recent_applications': [
                {'name': 'John Doe', 'position': 'Software Engineer', 'status': 'Under Review'},
                {'name': 'Jane Smith', 'position': 'Data Analyst', 'status': 'Shortlisted'},
                {'name': 'Mike Johnson', 'position': 'UI Designer', 'status': 'New'},
            ]
        }
        return render(request, 'accounts/recruiter_dashboard.html', context)
    else:
        context = {
            'user': user,
            'total_applications': 4,
            'under_review': 2,
            'interviews': 1,
            'rejected': 1,
            'job_applications': [
                {'title': 'Software Engineer', 'company': 'Tech Corp', 'status': 'Under Review', 'date': '2024-01-15'},
                {'title': 'Data Analyst', 'company': 'Data Inc', 'status': 'Shortlisted', 'date': '2024-01-10'},
                {'title': 'UI Designer', 'company': 'Design Studio', 'status': 'New', 'date': '2024-01-05'},
            ]
        }
        return render(request, 'accounts/candidate_dashboard.html', context)

@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {'user': request.user})