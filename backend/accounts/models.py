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
    resume_text = models.TextField(blank=True, null=True)  # Store extracted text
    skills = models.TextField(blank=True, null=True)  # Store extracted skills
    experience_years = models.IntegerField(null=True, blank=True)  # Extracted experience
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