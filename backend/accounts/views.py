from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile, Job, JobApplication
from .resume_parser import parse_resume

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        role = request.POST.get('role', 'candidate')
        
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
        jobs = Job.objects.filter(created_by=user)
        total_applications = JobApplication.objects.filter(job__created_by=user).count()
        
        context = {
            'user': user,
            'total_jobs': jobs.count(),
            'total_applications': total_applications,
            'shortlisted': JobApplication.objects.filter(job__created_by=user, status='shortlisted').count(),
            'interviews_scheduled': JobApplication.objects.filter(job__created_by=user, status='interview').count(),
            'jobs': jobs
        }
        return render(request, 'accounts/recruiter_dashboard.html', context)
    else:
        applications = JobApplication.objects.filter(candidate=user)
        available_jobs = Job.objects.filter(status='active')
        
        context = {
            'user': user,
            'total_applications': applications.count(),
            'under_review': applications.filter(status='pending').count(),
            'interviews': applications.filter(status='interview').count(),
            'rejected': applications.filter(status='rejected').count(),
            'applications': applications,
            'available_jobs': available_jobs
        }
        return render(request, 'accounts/candidate_dashboard.html', context)

@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {'user': request.user})

@login_required
def create_job(request):
    if request.user.profile.role != 'recruiter':
        messages.error(request, 'Only recruiters can post jobs!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        company = request.POST.get('company')
        location = request.POST.get('location')
        description = request.POST.get('description')
        requirements = request.POST.get('requirements')
        experience_level = request.POST.get('experience_level')
        salary_min = request.POST.get('salary_min')
        salary_max = request.POST.get('salary_max')
        status = request.POST.get('status', 'active')
        
        if not title or not company or not location or not description or not requirements:
            messages.error(request, 'All fields are required!')
            return render(request, 'accounts/create_job.html')
        
        try:
            job = Job.objects.create(
                title=title,
                company=company,
                location=location,
                description=description,
                requirements=requirements,
                experience_level=experience_level,
                salary_min=salary_min or None,
                salary_max=salary_max or None,
                status=status,
                created_by=request.user
            )
            messages.success(request, f'Job "{job.title}" created successfully!')
            return redirect('view_jobs')
        except Exception as e:
            messages.error(request, f'Error creating job: {str(e)}')
            return render(request, 'accounts/create_job.html')
    
    return render(request, 'accounts/create_job.html')

@login_required
def view_jobs(request):
    jobs = Job.objects.filter(status='active')
    return render(request, 'accounts/view_jobs.html', {'jobs': jobs})

@login_required
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    has_applied = False
    if request.user.profile.role == 'candidate':
        has_applied = JobApplication.objects.filter(job=job, candidate=request.user).exists()
    
    return render(request, 'accounts/job_detail.html', {
        'job': job,
        'has_applied': has_applied
    })

@login_required
def my_jobs(request):
    if request.user.profile.role != 'recruiter':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    jobs = Job.objects.filter(created_by=request.user)
    return render(request, 'accounts/my_jobs.html', {'jobs': jobs})

@login_required
def apply_job(request, job_id):
    if request.user.profile.role != 'candidate':
        messages.error(request, 'Only candidates can apply for jobs!')
        return redirect('dashboard')
    
    job = get_object_or_404(Job, id=job_id)
    
    if JobApplication.objects.filter(job=job, candidate=request.user).exists():
        messages.error(request, 'You have already applied for this job!')
        return redirect('job_detail', job_id=job.id)
    
    if request.method == 'POST':
        cover_letter = request.POST.get('cover_letter')
        
        try:
            application = JobApplication.objects.create(
                job=job,
                candidate=request.user,
                cover_letter=cover_letter,
                status='pending'
            )
            messages.success(request, f'Your application for "{job.title}" has been submitted successfully!')
            return redirect('job_detail', job_id=job.id)
        except Exception as e:
            messages.error(request, f'Error submitting application: {str(e)}')
            return render(request, 'accounts/apply_job.html', {'job': job})
    
    return render(request, 'accounts/apply_job.html', {'job': job})

@login_required
def job_applications(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    if job.created_by != request.user:
        messages.error(request, 'You are not authorized to view applications for this job!')
        return redirect('dashboard')
    
    applications = JobApplication.objects.filter(job=job)
    return render(request, 'accounts/job_applications.html', {
        'job': job,
        'applications': applications
    })

@login_required
def update_application_status(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id)
    

    if application.job.created_by != request.user:
        messages.error(request, 'You are not authorized to update this application!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if status:
            application.status = status
            application.notes = notes
            application.save()
            messages.success(request, f'Application status updated to {application.get_status_display()}')
        
        return redirect('job_applications', job_id=application.job.id)
    
    return redirect('job_applications', job_id=application.job.id)

@login_required
def my_applications(request):
    if request.user.profile.role != 'candidate':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    applications = JobApplication.objects.filter(candidate=request.user)
    return render(request, 'accounts/my_applications.html', {'applications': applications})


@login_required
def upload_resume(request):
    if request.user.profile.role != 'candidate':
        messages.error(request, 'Only candidates can upload resumes!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        resume_file = request.FILES.get('resume')
        
        if not resume_file:
            messages.error(request, 'Please select a file to upload!')
            return render(request, 'accounts/upload_resume.html')
        
        if resume_file.size > 5 * 1024 * 1024:
            messages.error(request, 'File size should be less than 5MB!')
            return render(request, 'accounts/upload_resume.html')
        
        allowed_extensions = ['.pdf', '.docx', '.doc', '.txt']
        file_name = resume_file.name.lower()
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            messages.error(request, 'Please upload PDF, DOCX, DOC, or TXT files only!')
            return render(request, 'accounts/upload_resume.html')
        
        try:
            parsed_data = parse_resume(resume_file)
            
            if parsed_data['success']:
                profile = request.user.profile
                profile.resume = resume_file
                profile.resume_text = parsed_data['text'][:5000]  
                profile.skills = ', '.join(parsed_data['skills'])
                profile.experience_years = parsed_data['experience_years']
                profile.save()
                
                messages.success(
                    request, 
                    f'Resume uploaded and parsed successfully! '
                    f'Found {len(parsed_data["skills"])} skills and {parsed_data["experience_years"]} years of experience.'
                )
                
                return render(request, 'accounts/upload_resume.html', {
                    'parsed_data': parsed_data,
                    'success': True
                })
            else:
                profile = request.user.profile
                profile.resume = resume_file
                profile.save()
                messages.warning(request, 'Resume uploaded but could not be parsed. Please try a different format.')
                
        except Exception as e:
            messages.error(request, f'Error uploading resume: {str(e)}')
    
    return render(request, 'accounts/upload_resume.html')

@login_required
def view_resume(request):
    if request.user.profile.role != 'candidate':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    profile = request.user.profile
    skills_list = profile.skills.split(', ') if profile.skills else []
    
    return render(request, 'accounts/view_resume.html', {
        'profile': profile,
        'skills': skills_list
    })

@login_required
def parse_application_resume(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id)
    
    if application.job.created_by != request.user:
        messages.error(request, 'You are not authorized to view this!')
        return redirect('dashboard')
    
    return render(request, 'accounts/application_resume.html', {
        'application': application
    })