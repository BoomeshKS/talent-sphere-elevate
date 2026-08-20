from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile, Job, JobApplication, Interview
from .resume_parser import parse_resume
from .matching_engine import calculate_match_score, get_experience_range, rank_candidates, auto_rank_and_update, get_matched_and_missing_skills, generate_recommendation


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
    matched_skills = []
    missing_skills = []
    
    if request.user.profile.role == 'candidate':
        has_applied = JobApplication.objects.filter(job=job, candidate=request.user).exists()
        
        profile = request.user.profile
        if profile.skills:
            matched_skills, missing_skills = get_matched_and_missing_skills(profile.skills, job)
    
    return render(request, 'accounts/job_detail.html', {
        'job': job,
        'has_applied': has_applied,
        'recruiter_name': job.created_by.username,
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'experience_range': get_experience_range(job.experience_level)
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
        manual_experience = request.POST.get('manual_experience', '')
        manual_skills = request.POST.get('manual_skills', '')
        
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
            
            profile = request.user.profile
            profile.resume = resume_file
            profile.resume_text = parsed_data['text'][:5000]
            
            if manual_skills:
                skills_list = [s.strip() for s in manual_skills.split(',') if s.strip()]
            else:
                skills_list = parsed_data['skills']
            
            profile.skills = ', '.join(skills_list)
            profile.experience_years = 0
            profile.save()
            
            applications = JobApplication.objects.filter(candidate=request.user)
            for app in applications:
                app.parsed_skills = profile.skills
                app.resume_text = profile.resume_text
                app.save()
            
            messages.success(
                request, 
                f'Resume uploaded successfully! Found {len(skills_list)} skills.'
            )
            
            return render(request, 'accounts/upload_resume.html', {
                'parsed_data': parsed_data,
                'success': True,
                'manual_skills': manual_skills
            })
            
        except Exception as e:
            messages.error(request, f'Error uploading resume: {str(e)}')
            return render(request, 'accounts/upload_resume.html')
    
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


@login_required
def analyze_application(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id)
    
    if application.job.created_by != request.user:
        messages.error(request, 'You are not authorized to view this!')
        return redirect('dashboard')
    
    scores = calculate_match_score(application)
    
    application.match_score = scores['overall_score']
    application.skill_match_score = scores['skill_score']
    application.experience_match_score = scores['experience_score']
    application.ai_recommendation = generate_recommendation(scores)
    application.save()
    
    return render(request, 'accounts/application_analysis.html', {
        'application': application,
        'scores': scores,
        'experience_range': get_experience_range(application.job.experience_level)
    })


@login_required
def rank_job_applications(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    if job.created_by != request.user:
        messages.error(request, 'You are not authorized to view this!')
        return redirect('dashboard')
    
    ranked_applications = auto_rank_and_update(job_id)
    
    return render(request, 'accounts/ranked_applications.html', {
        'job': job,
        'ranked_applications': ranked_applications
    })


@login_required
def bulk_analyze_applications(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    if job.created_by != request.user:
        messages.error(request, 'You are not authorized to view this!')
        return redirect('dashboard')
    
    applications = JobApplication.objects.filter(job=job)
    total = applications.count()
    analyzed = 0
    matches = []
    
    for application in applications:
        scores = calculate_match_score(application)
        application.match_score = scores['overall_score']
        application.skill_match_score = scores['skill_score']
        application.experience_match_score = scores['experience_score']
        application.ai_recommendation = generate_recommendation(scores)
        application.save()
        
        matches.append({
            'application': application,
            'scores': scores
        })
        analyzed += 1
    
    matches.sort(key=lambda x: x['scores']['overall_score'], reverse=True)
    
    messages.success(
        request, 
        f'Successfully analyzed {analyzed} out of {total} applications!'
    )
    
    return render(request, 'accounts/bulk_analysis.html', {
        'job': job,
        'matches': matches,
        'total': total,
        'analyzed': analyzed
    })


@login_required
def job_recommendations(request):
    if request.user.profile.role != 'candidate':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    candidate = request.user
    profile = candidate.profile
    active_jobs = Job.objects.filter(status='active')
    
    recommendations = []
    
    for job in active_jobs:
        if JobApplication.objects.filter(job=job, candidate=candidate).exists():
            continue
        
        if not profile.skills or not profile.experience_years:
            continue
        
        temp_app = JobApplication(
            job=job,
            candidate=candidate,
            parsed_skills=profile.skills,
            experience_years=profile.experience_years,
            resume_text=profile.resume_text or ""
        )
        
        scores = calculate_match_score(temp_app)
        
        if scores['overall_score'] >= 50:
            recommendations.append({
                'job': job,
                'scores': scores
            })
    
    recommendations.sort(key=lambda x: x['scores']['overall_score'], reverse=True)
    
    return render(request, 'accounts/job_recommendations.html', {
        'recommendations': recommendations[:10]
    })


@login_required
def update_resume_data(request):
    if request.user.profile.role != 'candidate':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        profile = request.user.profile
        skills = request.POST.get('skills', '')
        experience_years = request.POST.get('experience_years', '')
        
        if skills:
            skills_list = [s.strip() for s in skills.split(',') if s.strip()]
            profile.skills = ', '.join(skills_list)
        
        if not experience_years:
            messages.error(request, 'Please enter your years of experience!')
            return redirect('view_resume')
        
        try:
            profile.experience_years = float(experience_years)
        except:
            messages.error(request, 'Please enter a valid number for experience years!')
            return redirect('view_resume')
        
        profile.save()
        
        applications = JobApplication.objects.filter(candidate=request.user)
        for app in applications:
            app.parsed_skills = profile.skills
            app.experience_years = int(profile.experience_years) if profile.experience_years else None
            app.resume_text = profile.resume_text
            app.save()
        
        messages.success(request, 'Resume data updated successfully!')
        return redirect('view_resume')
    
    return redirect('view_resume')


def generate_recommendation(scores):
    overall = scores['overall_score']
    
    if overall >= 85:
        return "Highly Recommended - Excellent match for this position"
    elif overall >= 70:
        return "Recommended - Good match, suitable for this position"
    elif overall >= 55:
        return "Potentially Suitable - Consider for interview"
    elif overall >= 40:
        return "Average Match - May need additional training"
    else:
        return "Not Recommended - Low match score"





# Interview Parts


@login_required
def schedule_interview(request, application_id):
    """Schedule an interview for a candidate"""
    application = get_object_or_404(JobApplication, id=application_id)
    
    if application.job.created_by != request.user:
        messages.error(request, 'You are not authorized to schedule interviews for this job!')
        return redirect('dashboard')
    
    if application.status not in ['shortlisted', 'interview']:
        messages.error(request, 'This candidate must be shortlisted first!')
        return redirect('job_applications', job_id=application.job.id)
    
    if request.method == 'POST':
        interview_round = request.POST.get('interview_round')
        interview_mode = request.POST.get('interview_mode')
        scheduled_date = request.POST.get('scheduled_date')
        scheduled_time = request.POST.get('scheduled_time')
        duration_minutes = request.POST.get('duration_minutes', 60)
        meeting_link = request.POST.get('meeting_link', '')
        location = request.POST.get('location', '')
        notes = request.POST.get('notes', '')
        
        if not scheduled_date or not scheduled_time:
            messages.error(request, 'Please select date and time for the interview!')
            return render(request, 'accounts/schedule_interview.html', {'application': application})
        
        try:
            interview = Interview.objects.create(
                job_application=application,
                recruiter=request.user,
                candidate=application.candidate,
                interview_round=interview_round,
                interview_mode=interview_mode,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                duration_minutes=int(duration_minutes),
                meeting_link=meeting_link,
                location=location,
                notes=notes,
                status='scheduled'
            )
            
            application.status = 'interview'
            application.save()
            
            messages.success(request, f'Interview scheduled successfully for {application.candidate.username}!')
            return redirect('interview_detail', interview_id=interview.id)
        except Exception as e:
            messages.error(request, f'Error scheduling interview: {str(e)}')
    
    return render(request, 'accounts/schedule_interview.html', {'application': application})


@login_required
def interview_detail(request, interview_id):
    """View interview details"""
    interview = get_object_or_404(Interview, id=interview_id)
    
    if request.user != interview.recruiter and request.user != interview.candidate:
        messages.error(request, 'You are not authorized to view this interview!')
        return redirect('dashboard')
    
    return render(request, 'accounts/interview_detail.html', {'interview': interview})


@login_required
def my_interviews(request):
    """View all interviews for the logged-in user"""
    user = request.user
    
    if user.profile.role == 'recruiter':
        interviews = Interview.objects.filter(recruiter=user)
        title = 'My Scheduled Interviews (Recruiter)'
    else:
        interviews = Interview.objects.filter(candidate=user)
        title = 'My Interviews (Candidate)'
    
    upcoming = interviews.filter(status='scheduled').order_by('scheduled_date', 'scheduled_time')
    completed = interviews.filter(status='completed').order_by('-scheduled_date')
    cancelled = interviews.filter(status='cancelled').order_by('-scheduled_date')
    
    return render(request, 'accounts/my_interviews.html', {
        'interviews': interviews,
        'upcoming': upcoming,
        'completed': completed,
        'cancelled': cancelled,
        'title': title
    })


@login_required
def update_interview_status(request, interview_id):
    """Update interview status (completed, cancelled, rescheduled)"""
    interview = get_object_or_404(Interview, id=interview_id)
    
    if interview.recruiter != request.user:
        messages.error(request, 'You are not authorized to update this interview!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        status = request.POST.get('status')
        feedback = request.POST.get('feedback', '')
        feedback_score = request.POST.get('feedback_score', '')
        
        if status:
            interview.status = status
            
            if status == 'completed' and feedback:
                interview.feedback = feedback
                if feedback_score:
                    try:
                        interview.feedback_score = int(feedback_score)
                    except:
                        pass
                interview.feedback_submitted_at = timezone.now()
                
                application = interview.job_application
                if feedback_score and int(feedback_score) >= 7:
                    application.status = 'shortlisted'
                else:
                    application.status = 'reviewed'
                application.save()
            
            interview.save()
            messages.success(request, f'Interview status updated to {interview.get_status_display()}')
        
        return redirect('interview_detail', interview_id=interview.id)
    
    return redirect('interview_detail', interview_id=interview.id)


@login_required
def submit_interview_feedback(request, interview_id):
    """Submit feedback for an interview"""
    interview = get_object_or_404(Interview, id=interview_id)
    
    if interview.recruiter != request.user:
        messages.error(request, 'You are not authorized to submit feedback for this interview!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        feedback = request.POST.get('feedback')
        feedback_score = request.POST.get('feedback_score')
        
        if not feedback:
            messages.error(request, 'Please provide feedback!')
            return render(request, 'accounts/interview_feedback.html', {'interview': interview})
        
        interview.feedback = feedback
        if feedback_score:
            try:
                interview.feedback_score = int(feedback_score)
            except:
                pass
        interview.status = 'completed'
        interview.feedback_submitted_at = timezone.now()
        interview.save()
        
        application = interview.job_application
        if feedback_score and int(feedback_score) >= 7:
            application.status = 'shortlisted'
        else:
            application.status = 'reviewed'
        application.save()
        
        messages.success(request, 'Feedback submitted successfully!')
        return redirect('interview_detail', interview_id=interview.id)
    
    return render(request, 'accounts/interview_feedback.html', {'interview': interview})


@login_required
def reschedule_interview(request, interview_id):
    """Reschedule an interview"""
    interview = get_object_or_404(Interview, id=interview_id)
    
    if interview.recruiter != request.user:
        messages.error(request, 'You are not authorized to reschedule this interview!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        scheduled_date = request.POST.get('scheduled_date')
        scheduled_time = request.POST.get('scheduled_time')
        
        if not scheduled_date or not scheduled_time:
            messages.error(request, 'Please select new date and time!')
            return render(request, 'accounts/reschedule_interview.html', {'interview': interview})
        
        interview.scheduled_date = scheduled_date
        interview.scheduled_time = scheduled_time
        interview.status = 'rescheduled'
        interview.save()
        
        messages.success(request, 'Interview rescheduled successfully!')
        return redirect('interview_detail', interview_id=interview.id)
    
    return render(request, 'accounts/reschedule_interview.html', {'interview': interview})


@login_required
def cancel_interview(request, interview_id):
    """Cancel an interview"""
    interview = get_object_or_404(Interview, id=interview_id)
    
    if interview.recruiter != request.user:
        messages.error(request, 'You are not authorized to cancel this interview!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        interview.status = 'cancelled'
        interview.notes = f"Cancelled. Reason: {reason}" if reason else "Cancelled"
        interview.save()
        
        messages.success(request, 'Interview cancelled successfully!')
        return redirect('my_interviews')
    
    return render(request, 'accounts/cancel_interview.html', {'interview': interview})