from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('recruiter', 'Recruiter'),
        ('candidate', 'Candidate'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='candidate')
    phone = models.CharField(max_length=15, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    resume_text = models.TextField(blank=True, null=True) 
    skills = models.TextField(blank=True, null=True)  
    experience_years = models.IntegerField(null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Job(models.Model):
    JOB_STATUS = (
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('draft', 'Draft'),
    )
    
    EXPERIENCE_LEVELS = (
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('lead', 'Lead'),
        ('executive', 'Executive'),
    )
    
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField()
    required_skills = models.TextField(blank=True, null=True, help_text="Comma separated skills")
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS, default='mid')
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=JOB_STATUS, default='active')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} at {self.company}"
    
    class Meta:
        ordering = ['-created_at']


class JobApplication(models.Model):
    APPLICATION_STATUS = (
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('shortlisted', 'Shortlisted'),
        ('interview', 'Interview Scheduled'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField(blank=True, null=True)
    resume = models.FileField(upload_to='application_resumes/', blank=True, null=True)
    
    resume_text = models.TextField(blank=True, null=True)
    parsed_skills = models.TextField(blank=True, null=True, help_text="Extracted skills from resume")
    parsed_experience = models.TextField(blank=True, null=True, help_text="Extracted experience details")
    parsed_education = models.TextField(blank=True, null=True, help_text="Extracted education details")
    experience_years = models.IntegerField(null=True, blank=True, help_text="Total years of experience")
    
    match_score = models.IntegerField(null=True, blank=True, help_text="Overall match percentage")
    skill_match_score = models.IntegerField(null=True, blank=True, help_text="Skills match percentage")
    experience_match_score = models.IntegerField(null=True, blank=True, help_text="Experience match percentage")
    ai_recommendation = models.TextField(blank=True, null=True, help_text="AI generated recommendation")
    
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default='pending')
    notes = models.TextField(blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['job', 'candidate']
        ordering = ['-applied_at']
    
    def __str__(self):
        return f"{self.candidate.username} - {self.job.title}"



class Interview(models.Model):
    INTERVIEW_MODES = (
        ('online', 'Online - Video Call'),
        ('offline', 'Offline - In Person'),
        ('phone', 'Phone Call'),
    )
    
    INTERVIEW_ROUNDS = (
        ('round1', 'Round 1 - Screening'),
        ('round2', 'Round 2 - Technical'),
        ('round3', 'Round 3 - Managerial'),
        ('round4', 'Round 4 - HR'),
        ('round5', 'Final Round'),
    )
    
    INTERVIEW_STATUS = (
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
        ('no_show', 'No Show'),
    )
    
    job_application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='interviews')
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conducted_interviews')
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='candidate_interviews')
    
    interview_round = models.CharField(max_length=20, choices=INTERVIEW_ROUNDS, default='round1')
    interview_mode = models.CharField(max_length=20, choices=INTERVIEW_MODES, default='online')
    
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    duration_minutes = models.IntegerField(default=60)
    
    meeting_link = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=INTERVIEW_STATUS, default='scheduled')
    
    feedback = models.TextField(blank=True, null=True)
    feedback_score = models.IntegerField(null=True, blank=True, help_text="Score out of 10")
    feedback_submitted_at = models.DateTimeField(blank=True, null=True)
    
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_date', 'scheduled_time']
    
    def __str__(self):
        return f"{self.candidate.username} - {self.job_application.job.title} - {self.get_interview_round_display()}"
    
    def is_upcoming(self):
        from datetime import datetime, date
        from django.utils import timezone
        interview_datetime = datetime.combine(self.scheduled_date, self.scheduled_time)
        return interview_datetime > timezone.now() and self.status == 'scheduled'