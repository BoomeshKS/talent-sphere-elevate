from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('create-job/', views.create_job, name='create_job'),
    path('jobs/', views.view_jobs, name='view_jobs'),
    path('job/<int:job_id>/', views.job_detail, name='job_detail'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    path('apply/<int:job_id>/', views.apply_job, name='apply_job'),
    path('job/<int:job_id>/applications/', views.job_applications, name='job_applications'),
    path('application/<int:application_id>/update/', views.update_application_status, name='update_application_status'),
    path('my-applications/', views.my_applications, name='my_applications'),
]